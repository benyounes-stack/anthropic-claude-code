"""Chargement et validation de la configuration (`sites.yaml`).

La configuration décrit *les postes de travail*, pas les personnes : chaque zone
est un polygone dans le champ d'une caméra. Le système mesure l'occupation d'une
zone, il n'identifie personne. Voir README, section Conformité.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import time
from pathlib import Path

import yaml

_ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


class ConfigError(Exception):
    """Configuration invalide."""


@dataclass(frozen=True)
class Zone:
    """Un poste de travail, délimité dans l'image d'une caméra.

    `polygon` est en coordonnées normalisées (0.0–1.0), ce qui rend la zone
    indépendante de la résolution du flux : changer le profil d'encodage de la
    caméra ne casse pas la calibration.
    """

    id: str
    label: str
    polygon: tuple[tuple[float, float], ...]
    expected_headcount: int = 1
    # Alerte si la zone reste vide plus longtemps que ça pendant le quart.
    max_idle_minutes: int = 15

    def __post_init__(self) -> None:
        if len(self.polygon) < 3:
            raise ConfigError(
                f"zone {self.id}: un polygone demande au moins 3 points, "
                f"{len(self.polygon)} fourni(s)"
            )
        for x, y in self.polygon:
            if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
                raise ConfigError(
                    f"zone {self.id}: point ({x}, {y}) hors de [0,1] — les "
                    f"coordonnées sont normalisées, pas en pixels"
                )
        if self.expected_headcount < 1:
            raise ConfigError(f"zone {self.id}: expected_headcount doit être >= 1")


@dataclass(frozen=True)
class Camera:
    id: str
    host: str
    username: str
    password: str
    zones: tuple[Zone, ...]
    port: int = 80
    tls: bool = False
    channel: int = 1

    def __post_init__(self) -> None:
        if not self.zones:
            raise ConfigError(f"caméra {self.id}: aucune zone définie")
        seen: set[str] = set()
        for zone in self.zones:
            if zone.id in seen:
                raise ConfigError(f"caméra {self.id}: zone dupliquée '{zone.id}'")
            seen.add(zone.id)


@dataclass(frozen=True)
class Shift:
    """Un quart de travail. Les rapports sont bornés par ces plages."""

    id: str
    label: str
    start: time
    end: time
    # 0 = lundi … 6 = dimanche (comme `date.weekday()`).
    weekdays: tuple[int, ...] = (0, 1, 2, 3, 4)

    def __post_init__(self) -> None:
        if self.start == self.end:
            raise ConfigError(f"quart {self.id}: start et end sont identiques")
        for day in self.weekdays:
            if not 0 <= day <= 6:
                raise ConfigError(f"quart {self.id}: jour invalide {day} (0–6 attendu)")

    @property
    def crosses_midnight(self) -> bool:
        return self.end < self.start


@dataclass(frozen=True)
class Site:
    id: str
    label: str
    cameras: tuple[Camera, ...]
    shifts: tuple[Shift, ...]
    timezone: str = "Africa/Algiers"

    def zones(self) -> list[tuple[Camera, Zone]]:
        return [(camera, zone) for camera in self.cameras for zone in camera.zones]


@dataclass(frozen=True)
class DetectorConfig:
    model_path: str = ""
    confidence: float = 0.35
    nms_iou: float = 0.45
    input_size: int = 640


@dataclass(frozen=True)
class WhatsAppConfig:
    phone_number_id: str = ""
    access_token: str = ""
    recipients: tuple[str, ...] = ()
    template_name: str = "rapport_fin_de_journee"
    language_code: str = "fr"
    graph_version: str = "v23.0"
    # Interdit par défaut : mettre des noms d'employés dans le message revient à
    # transférer des données personnelles hors d'Algérie (serveurs Meta).
    # Voir README, section Conformité, avant de passer ça à true.
    include_employee_names: bool = False


@dataclass(frozen=True)
class Config:
    sites: tuple[Site, ...]
    detector: DetectorConfig = field(default_factory=DetectorConfig)
    whatsapp: WhatsAppConfig = field(default_factory=WhatsAppConfig)
    database_path: str = "data/workforce.db"
    sample_interval_seconds: int = 15
    # Purge automatique. Les échantillons ne contiennent aucune image, mais la
    # minimisation reste une obligation (loi 25-11, art. sur la conservation).
    retention_days: int = 90

    def site(self, site_id: str) -> Site:
        for site in self.sites:
            if site.id == site_id:
                return site
        raise ConfigError(f"site inconnu: {site_id}")


def _expand_env(value: object) -> object:
    """Remplace `${VAR}` par la variable d'environnement correspondante.

    Les mots de passe caméra et le token Meta ne doivent pas vivre dans le YAML.
    """
    if isinstance(value, str):

        def replace(match: re.Match[str]) -> str:
            name = match.group(1)
            resolved = os.environ.get(name)
            if resolved is None:
                raise ConfigError(
                    f"variable d'environnement manquante: {name} "
                    f"(référencée dans la configuration)"
                )
            return resolved

        return _ENV_PATTERN.sub(replace, value)
    if isinstance(value, dict):
        return {key: _expand_env(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_expand_env(item) for item in value]
    return value


def _parse_time(raw: object, context: str) -> time:
    if isinstance(raw, time):
        return raw
    if not isinstance(raw, str):
        raise ConfigError(f"{context}: heure attendue au format HH:MM, reçu {raw!r}")
    try:
        hours, _, minutes = raw.partition(":")
        return time(int(hours), int(minutes))
    except ValueError as exc:
        raise ConfigError(f"{context}: heure invalide {raw!r}") from exc


def _parse_polygon(raw: object, context: str) -> tuple[tuple[float, float], ...]:
    if not isinstance(raw, list):
        raise ConfigError(f"{context}: polygon doit être une liste de paires [x, y]")
    points: list[tuple[float, float]] = []
    for point in raw:
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise ConfigError(f"{context}: point invalide {point!r}, [x, y] attendu")
        points.append((float(point[0]), float(point[1])))
    return tuple(points)


def load_config(path: str | Path) -> Config:
    """Charge et valide la configuration. Lève `ConfigError` au premier problème."""
    path = Path(path)
    if not path.is_file():
        raise ConfigError(f"configuration introuvable: {path}")
    with path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    if not isinstance(raw, dict):
        raise ConfigError(f"{path}: le document YAML doit être un mapping")
    raw = _expand_env(raw)
    return _build_config(raw)


def _build_config(raw: dict) -> Config:
    raw_sites = raw.get("sites")
    if not isinstance(raw_sites, list) or not raw_sites:
        raise ConfigError("au moins un site doit être défini sous `sites:`")

    sites: list[Site] = []
    for raw_site in raw_sites:
        site_id = str(raw_site.get("id") or "")
        if not site_id:
            raise ConfigError("chaque site doit avoir un `id`")

        cameras: list[Camera] = []
        for raw_camera in raw_site.get("cameras") or []:
            camera_id = str(raw_camera.get("id") or "")
            context = f"site {site_id} / caméra {camera_id or '?'}"
            if not camera_id:
                raise ConfigError(f"{context}: `id` manquant")
            for required in ("host", "username", "password"):
                if not raw_camera.get(required):
                    raise ConfigError(f"{context}: `{required}` manquant")

            zones = tuple(
                Zone(
                    id=str(raw_zone["id"]),
                    label=str(raw_zone.get("label") or raw_zone["id"]),
                    polygon=_parse_polygon(
                        raw_zone.get("polygon"), f"{context} / zone {raw_zone.get('id')}"
                    ),
                    expected_headcount=int(raw_zone.get("expected_headcount", 1)),
                    max_idle_minutes=int(raw_zone.get("max_idle_minutes", 15)),
                )
                for raw_zone in raw_camera.get("zones") or []
            )
            cameras.append(
                Camera(
                    id=camera_id,
                    host=str(raw_camera["host"]),
                    username=str(raw_camera["username"]),
                    password=str(raw_camera["password"]),
                    zones=zones,
                    port=int(raw_camera.get("port", 80)),
                    tls=bool(raw_camera.get("tls", False)),
                    channel=int(raw_camera.get("channel", 1)),
                )
            )
        if not cameras:
            raise ConfigError(f"site {site_id}: aucune caméra définie")

        shifts = tuple(
            Shift(
                id=str(raw_shift["id"]),
                label=str(raw_shift.get("label") or raw_shift["id"]),
                start=_parse_time(raw_shift.get("start"), f"quart {raw_shift.get('id')}"),
                end=_parse_time(raw_shift.get("end"), f"quart {raw_shift.get('id')}"),
                weekdays=tuple(int(day) for day in raw_shift.get("weekdays", [0, 1, 2, 3, 4])),
            )
            for raw_shift in raw_site.get("shifts") or []
        )
        if not shifts:
            raise ConfigError(f"site {site_id}: aucun quart défini sous `shifts:`")

        # Les identifiants de zone doivent être uniques à l'échelle du site :
        # le rapport les agrège toutes caméras confondues.
        seen_zones: set[str] = set()
        for camera in cameras:
            for zone in camera.zones:
                if zone.id in seen_zones:
                    raise ConfigError(
                        f"site {site_id}: identifiant de zone dupliqué '{zone.id}' "
                        f"(les zones doivent être uniques par site, pas par caméra)"
                    )
                seen_zones.add(zone.id)

        sites.append(
            Site(
                id=site_id,
                label=str(raw_site.get("label") or site_id),
                cameras=tuple(cameras),
                shifts=shifts,
                timezone=str(raw_site.get("timezone") or "Africa/Algiers"),
            )
        )

    raw_detector = raw.get("detector") or {}
    detector = DetectorConfig(
        model_path=str(raw_detector.get("model_path") or ""),
        confidence=float(raw_detector.get("confidence", 0.35)),
        nms_iou=float(raw_detector.get("nms_iou", 0.45)),
        input_size=int(raw_detector.get("input_size", 640)),
    )

    raw_whatsapp = raw.get("whatsapp") or {}
    whatsapp = WhatsAppConfig(
        phone_number_id=str(raw_whatsapp.get("phone_number_id") or ""),
        access_token=str(raw_whatsapp.get("access_token") or ""),
        recipients=tuple(str(number) for number in raw_whatsapp.get("recipients") or []),
        template_name=str(raw_whatsapp.get("template_name") or "rapport_fin_de_journee"),
        language_code=str(raw_whatsapp.get("language_code") or "fr"),
        graph_version=str(raw_whatsapp.get("graph_version") or "v23.0"),
        include_employee_names=bool(raw_whatsapp.get("include_employee_names", False)),
    )

    interval = int(raw.get("sample_interval_seconds", 15))
    if interval < 5:
        raise ConfigError(
            "sample_interval_seconds < 5 : cadence trop agressive pour les "
            "caméras et inutile pour mesurer une occupation de poste"
        )

    return Config(
        sites=tuple(sites),
        detector=detector,
        whatsapp=whatsapp,
        database_path=str(raw.get("database_path") or "data/workforce.db"),
        sample_interval_seconds=interval,
        retention_days=int(raw.get("retention_days", 90)),
    )
