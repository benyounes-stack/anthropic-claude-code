"""Boucle de collecte : snapshot → détection → occupation par zone → SQLite.

La collecte n'a lieu que pendant les quarts déclarés. Hors quart, aucune image
n'est demandée aux caméras : c'est à la fois une économie de charge et une
application du principe de minimisation (on ne mesure pas les gens en dehors de
leur temps de travail).
"""

from __future__ import annotations

import asyncio
import logging
import time as time_module
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from .config import Camera, Config, Site
from .dahua import DahuaClient, DahuaError
from .detect import PersonDetector, assign_to_zones
from .report import shift_window, shifts_for_date
from .store import Sample, Store

_LOGGER = logging.getLogger(__name__)

# Marge autour du quart : capte l'arrivée anticipée et le départ tardif, ce qui
# rend le premier/dernier passage exploitable comme repère de présence.
_SHIFT_MARGIN = timedelta(minutes=15)


def is_within_active_shift(site: Site, moment: datetime) -> bool:
    """La collecte est-elle autorisée à cet instant pour ce site ?"""
    local = moment.astimezone(ZoneInfo(site.timezone))
    # Un quart de nuit démarré la veille court encore : on teste les deux dates.
    for offset in (0, -1):
        candidate_date = local.date() + timedelta(days=offset)
        for shift in shifts_for_date(site, candidate_date):
            start, end = shift_window(site, shift, candidate_date)
            if start - _SHIFT_MARGIN <= local <= end + _SHIFT_MARGIN:
                return True
    return False


async def sample_camera(
    client: DahuaClient,
    camera: Camera,
    detector: PersonDetector,
    site_id: str,
    ts: int,
) -> list[Sample]:
    """Un échantillon pour une caméra : toutes ses zones, au même horodatage.

    L'inférence part dans un thread : elle est bornée CPU et bloquerait sinon la
    boucle d'événements pendant que les autres caméras attendent leur snapshot.
    """
    jpeg = await client.snapshot(camera.channel)
    detections = await asyncio.to_thread(detector.detect, jpeg)
    # `jpeg` sort du scope ici : l'image n'est jamais persistée.
    zones = [(zone.id, zone.polygon) for zone in camera.zones]
    counts = assign_to_zones(detections, zones)
    return [
        Sample(ts=ts, site=site_id, zone=zone_id, person_count=count)
        for zone_id, count in counts.items()
    ]


async def collect_once(
    site: Site,
    clients: dict[str, DahuaClient],
    detector: PersonDetector,
    store: Store,
) -> tuple[int, int]:
    """Un tour de collecte sur toutes les caméras d'un site.

    Retourne `(échantillons écrits, caméras en échec)`. Une caméra injoignable
    est tracée dans `collection_errors` et n'écrit *aucun* échantillon — surtout
    pas un zéro, qui serait lu comme un poste vide.
    """
    ts = int(time_module.time())
    results = await asyncio.gather(
        *(
            sample_camera(clients[camera.id], camera, detector, site.id, ts)
            for camera in site.cameras
        ),
        return_exceptions=True,
    )

    samples: list[Sample] = []
    failures = 0
    for camera, result in zip(site.cameras, results):
        if isinstance(result, BaseException):
            failures += 1
            message = str(result) or result.__class__.__name__
            _LOGGER.warning("collecte échouée sur %s: %s", camera.id, message)
            store.record_error(ts, site.id, camera.id, message)
            continue
        samples.extend(result)

    written = store.record_samples(samples)
    return written, failures


async def run_collector(
    config: Config,
    site_id: str | None = None,
    stop_event: asyncio.Event | None = None,
    max_iterations: int | None = None,
) -> None:
    """Boucle principale. Tourne jusqu'à `stop_event` ou `max_iterations`.

    La cadence est calée sur l'horloge murale : on dort le temps restant jusqu'au
    prochain multiple de l'intervalle, ce qui évite la dérive lente d'un
    `sleep(interval)` naïf et garde les échantillons alignés entre caméras.
    """
    from .detect import build_detector  # import différé (onnxruntime optionnel)

    sites = [config.site(site_id)] if site_id else list(config.sites)
    detector = build_detector(
        config.detector.model_path,
        config.detector.confidence,
        config.detector.nms_iou,
        config.detector.input_size,
    )
    stop_event = stop_event or asyncio.Event()
    interval = config.sample_interval_seconds

    clients: dict[str, DahuaClient] = {}
    for site in sites:
        for camera in site.cameras:
            clients[camera.id] = DahuaClient(
                host=camera.host,
                username=camera.username,
                password=camera.password,
                port=camera.port,
                tls=camera.tls,
            )

    iterations = 0
    try:
        with Store(config.database_path) as store:
            _purge_expired(store, config)
            while not stop_event.is_set():
                now = datetime.now(tz=ZoneInfo("UTC"))
                active_sites = [site for site in sites if is_within_active_shift(site, now)]

                if active_sites:
                    for site in active_sites:
                        written, failures = await collect_once(
                            site, clients, detector, store
                        )
                        _LOGGER.info(
                            "%s: %d échantillon(s) écrit(s), %d caméra(s) en échec",
                            site.id,
                            written,
                            failures,
                        )
                else:
                    _LOGGER.debug("hors quart : aucune collecte")

                iterations += 1
                if max_iterations is not None and iterations >= max_iterations:
                    break

                await _sleep_to_next_tick(interval, stop_event)
    finally:
        await asyncio.gather(
            *(client.aclose() for client in clients.values()), return_exceptions=True
        )


async def _sleep_to_next_tick(interval: int, stop_event: asyncio.Event) -> None:
    """Dort jusqu'au prochain top d'horloge, interruptible par `stop_event`."""
    now = time_module.time()
    delay = interval - (now % interval)
    try:
        await asyncio.wait_for(stop_event.wait(), timeout=delay)
    except asyncio.TimeoutError:
        pass


def _purge_expired(store: Store, config: Config) -> None:
    if config.retention_days <= 0:
        return
    cutoff = int(time_module.time()) - config.retention_days * 86400
    removed = store.purge_before(cutoff)
    if removed:
        _LOGGER.info(
            "purge: %d ligne(s) supprimée(s) au-delà de %d jours de conservation",
            removed,
            config.retention_days,
        )


async def probe_cameras(config: Config, site_id: str | None = None) -> list[dict]:
    """Teste la liaison et les identifiants de chaque caméra. Ne mesure rien.

    À lancer en premier après l'installation : distingue un problème réseau /
    identifiants d'un problème de calibration de zones.
    """
    sites = [config.site(site_id)] if site_id else list(config.sites)
    results: list[dict] = []
    for site in sites:
        for camera in site.cameras:
            entry: dict = {"site": site.id, "camera": camera.id, "host": camera.host}
            client = DahuaClient(
                host=camera.host,
                username=camera.username,
                password=camera.password,
                port=camera.port,
                tls=camera.tls,
            )
            try:
                info = await client.device_info()
                jpeg = await client.snapshot(camera.channel)
                entry.update(
                    ok=True,
                    device_type=info.device_type,
                    firmware=info.software_version,
                    serial=info.serial_no,
                    snapshot_bytes=len(jpeg),
                    zones=[zone.id for zone in camera.zones],
                )
            except DahuaError as exc:
                entry.update(ok=False, error=str(exc))
            except Exception as exc:  # pragma: no cover - défensif
                entry.update(ok=False, error=f"{exc.__class__.__name__}: {exc}")
            finally:
                await client.aclose()
            results.append(entry)
    return results


def today_in_site_timezone(site: Site) -> date:
    return datetime.now(tz=ZoneInfo(site.timezone)).date()
