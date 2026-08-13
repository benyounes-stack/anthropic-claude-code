"""Client HTTP pour équipements Dahua (IPC / NVR / XVR).

Parle l'API CGI Dahua en authentification digest. Volontairement limité à ce
dont le collecteur a besoin : identification de l'équipement, snapshot ponctuel,
lecture de config, et flux d'événements.

Principe de conception : aucune image n'est écrite sur disque par ce module.
`snapshot()` retourne les octets JPEG en mémoire, le détecteur les consomme et
seul le compte de personnes par zone est persisté.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import AsyncIterator

import httpx

_LOGGER = logging.getLogger(__name__)

# Dahua renvoie parfois un 401 sur la première requête d'une connexion réutilisée
# même avec des identifiants valides ; un retry immédiat suffit.
_AUTH_RETRIES = 1


class DahuaError(Exception):
    """Échec d'un appel à l'API Dahua."""


class DahuaAuthError(DahuaError):
    """Identifiants refusés par l'équipement."""


@dataclass(frozen=True)
class DeviceInfo:
    device_type: str
    serial_no: str
    software_version: str
    machine_name: str


class DahuaClient:
    """Client asynchrone pour un équipement Dahua.

    Args:
        host: IP ou nom d'hôte de l'équipement.
        username / password: compte de l'équipement. Utiliser un compte dédié
            en lecture seule — voir le README, section Sécurité.
        port: port HTTP (80 par défaut, 443 en TLS).
        tls: passer en HTTPS. Les certificats auto-signés des caméras ne sont
            pas vérifiables, d'où `verify=False` ; le lien reste chiffré.
        timeout: timeout par requête, en secondes.
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 80,
        tls: bool = False,
        timeout: float = 10.0,
    ) -> None:
        self.host = host
        self.port = port
        scheme = "https" if tls else "http"
        self._base = f"{scheme}://{host}:{port}"
        self._client = httpx.AsyncClient(
            auth=httpx.DigestAuth(username, password),
            timeout=timeout,
            verify=False if tls else True,
            # Les caméras plafonnent le nombre de sessions HTTP simultanées.
            limits=httpx.Limits(max_connections=2, max_keepalive_connections=1),
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "DahuaClient":
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    # ------------------------------------------------------------------ requêtes

    async def _get(self, path: str) -> httpx.Response:
        url = f"{self._base}{path}"
        last_exc: Exception | None = None
        for attempt in range(_AUTH_RETRIES + 1):
            try:
                response = await self._client.get(url)
            except httpx.HTTPError as exc:  # réseau, DNS, timeout
                raise DahuaError(f"{self.host}: {exc}") from exc
            if response.status_code == 401:
                last_exc = DahuaAuthError(
                    f"{self.host}: identifiants refusés (401) sur {path}"
                )
                if attempt < _AUTH_RETRIES:
                    await asyncio.sleep(0.2)
                    continue
                raise last_exc
            if response.status_code >= 400:
                raise DahuaError(
                    f"{self.host}: HTTP {response.status_code} sur {path}"
                )
            return response
        raise last_exc or DahuaError(f"{self.host}: échec sur {path}")

    async def _get_text(self, path: str) -> str:
        return (await self._get(path)).text

    # -------------------------------------------------------------- équipement

    async def device_type(self) -> str:
        raw = await self._get_text("/cgi-bin/magicBox.cgi?action=getDeviceType")
        return parse_cgi_body(raw).get("type", "").strip()

    async def serial_no(self) -> str:
        raw = await self._get_text("/cgi-bin/magicBox.cgi?action=getSerialNo")
        return parse_cgi_body(raw).get("sn", "").strip()

    async def software_version(self) -> str:
        raw = await self._get_text("/cgi-bin/magicBox.cgi?action=getSoftwareVersion")
        return parse_cgi_body(raw).get("version", "").strip()

    async def machine_name(self) -> str:
        raw = await self._get_text("/cgi-bin/magicBox.cgi?action=getMachineName")
        body = parse_cgi_body(raw)
        return (body.get("name") or body.get("machineName") or "").strip()

    async def device_info(self) -> DeviceInfo:
        """Identifie l'équipement. Sert de test de connectivité au démarrage."""
        device_type, serial, version, name = await asyncio.gather(
            self.device_type(),
            self.serial_no(),
            self.software_version(),
            self.machine_name(),
        )
        return DeviceInfo(device_type, serial, version, name)

    async def get_config(self, name: str) -> dict[str, str]:
        """Lit une section de configuration (`MotionDetect`, `NTP`, `General`…)."""
        raw = await self._get_text(
            f"/cgi-bin/configManager.cgi?action=getConfig&name={name}"
        )
        return parse_cgi_body(raw)

    # ---------------------------------------------------------------- snapshot

    async def snapshot(self, channel: int = 1) -> bytes:
        """Capture une image JPEG.

        `channel` est indexé à partir de 1 : pour une caméra IP c'est toujours 1,
        pour un NVR/XVR c'est le numéro de canal affiché dans l'interface.

        Les octets ne sont jamais écrits sur disque par ce module.
        """
        response = await self._get(f"/cgi-bin/snapshot.cgi?channel={channel}")
        payload = response.content
        if not payload:
            raise DahuaError(f"{self.host}: snapshot vide (canal {channel})")
        # Certains firmwares répondent 200 avec un corps d'erreur texte.
        if not payload.startswith(b"\xff\xd8"):
            raise DahuaError(
                f"{self.host}: réponse non-JPEG sur le canal {channel} "
                f"({payload[:60]!r})"
            )
        return payload

    # ------------------------------------------------------------- événements

    async def events(
        self, codes: list[str] | None = None, heartbeat: int = 20
    ) -> AsyncIterator[dict[str, str]]:
        """Flux d'événements temps réel via `eventManager.cgi?action=attach`.

        Non utilisé par le collecteur par défaut (qui échantillonne des
        snapshots), mais disponible pour la variante « IVS embarqué » décrite
        dans le README : les caméras WizSense/WizMind classifient l'humain
        directement à bord et n'ont donc pas besoin de détecteur logiciel.

        Yield un dict par événement, ex. `{"Code": "SmartMotionHuman",
        "action": "Start", "index": "0"}`.
        """
        code_list = ",".join(codes or ["All"])
        path = (
            f"/cgi-bin/eventManager.cgi?action=attach&codes=[{code_list}]"
            f"&heartbeat={heartbeat}"
        )
        url = f"{self._base}{path}"
        try:
            async with self._client.stream("GET", url, timeout=None) as response:
                if response.status_code == 401:
                    raise DahuaAuthError(f"{self.host}: identifiants refusés (401)")
                if response.status_code >= 400:
                    raise DahuaError(
                        f"{self.host}: HTTP {response.status_code} sur le flux"
                    )
                async for line in response.aiter_lines():
                    event = _parse_event_line(line)
                    if event is not None:
                        yield event
        except httpx.HTTPError as exc:
            raise DahuaError(f"{self.host}: flux d'événements interrompu: {exc}") from exc


def parse_cgi_body(raw: str) -> dict[str, str]:
    """Convertit un corps CGI Dahua (`clé=valeur` par ligne) en dict.

    Les clés Dahua sont préfixées (`table.General.MachineName=cam1`) ; on
    conserve la forme complète *et* le dernier segment, ce qui permet
    d'interroger indifféremment `"table.General.MachineName"` ou `"MachineName"`.
    """
    parsed: dict[str, str] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        parsed[key] = value
        tail = key.rsplit(".", 1)[-1]
        parsed.setdefault(tail, value)
    return parsed


def _parse_event_line(line: str) -> dict[str, str] | None:
    """Extrait un événement d'une ligne du flux multipart.

    Les lignes utiles ont la forme `Code=VideoMotion;action=Start;index=0`.
    Les frontières multipart, en-têtes et heartbeats sont ignorés.
    """
    line = line.strip()
    if not line.startswith("Code="):
        return None
    event: dict[str, str] = {}
    for part in line.split(";"):
        key, _, value = part.partition("=")
        if key:
            event[key.strip()] = value.strip()
    return event or None
