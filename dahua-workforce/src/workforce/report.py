"""Agrégation de fin de journée : échantillons brut → indicateurs par poste.

Deux règles gouvernent ce module :

1. **Un trou de données n'est pas une absence.** Si la caméra était injoignable,
   les échantillons manquent ; on ne les compte ni comme occupés ni comme vides,
   et on remonte le taux de couverture pour que le lecteur sache ce qu'il regarde.
2. **Rien n'est nominatif.** Les indicateurs portent sur des postes de travail.
   La correspondance poste → employé, si elle existe, vit dans la feuille
   d'affectation du chef d'équipe, pas ici.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from .config import Config, Shift, Site, Zone
from .store import Sample, Store

# En dessous de ce taux de couverture, les chiffres d'un poste ne sont plus
# présentés comme mesurés mais comme partiels.
COVERAGE_WARNING_THRESHOLD = 0.90


@dataclass(frozen=True)
class ZoneReport:
    zone_id: str
    label: str
    expected_headcount: int
    max_idle_minutes: int
    expected_samples: int
    received_samples: int
    occupied_samples: int
    fully_staffed_samples: int
    unoccupied_minutes: float
    longest_idle_minutes: float
    first_seen_local: str | None
    last_seen_local: str | None

    @property
    def coverage(self) -> float:
        """Part des échantillons attendus qui ont effectivement été collectés."""
        if self.expected_samples == 0:
            return 0.0
        return min(1.0, self.received_samples / self.expected_samples)

    @property
    def occupancy_rate(self) -> float:
        """Part du temps *mesuré* où au moins une personne était au poste."""
        if self.received_samples == 0:
            return 0.0
        return self.occupied_samples / self.received_samples

    @property
    def fully_staffed_rate(self) -> float:
        """Part du temps mesuré où l'effectif attendu était au complet."""
        if self.received_samples == 0:
            return 0.0
        return self.fully_staffed_samples / self.received_samples

    @property
    def is_reliable(self) -> bool:
        return self.coverage >= COVERAGE_WARNING_THRESHOLD

    @property
    def breached_idle_threshold(self) -> bool:
        return self.longest_idle_minutes > self.max_idle_minutes


@dataclass(frozen=True)
class SiteReport:
    site_id: str
    site_label: str
    report_date: date
    shift_id: str
    shift_label: str
    window_start_local: str
    window_end_local: str
    timezone: str
    sample_interval_seconds: int
    zones: tuple[ZoneReport, ...]
    collection_errors: tuple[tuple[str, str, int], ...] = field(default=())

    @property
    def overall_occupancy_rate(self) -> float:
        """Occupation agrégée, pondérée par le nombre d'échantillons de chaque poste."""
        received = sum(zone.received_samples for zone in self.zones)
        if received == 0:
            return 0.0
        return sum(zone.occupied_samples for zone in self.zones) / received

    @property
    def zones_with_alerts(self) -> tuple[ZoneReport, ...]:
        return tuple(zone for zone in self.zones if zone.breached_idle_threshold)

    @property
    def unreliable_zones(self) -> tuple[ZoneReport, ...]:
        return tuple(zone for zone in self.zones if not zone.is_reliable)

    @property
    def has_data(self) -> bool:
        return any(zone.received_samples > 0 for zone in self.zones)


def shift_window(
    site: Site, shift: Shift, report_date: date
) -> tuple[datetime, datetime]:
    """Bornes locales d'un quart pour une date donnée.

    Un quart de nuit (`end < start`) se termine le lendemain.
    """
    tz = ZoneInfo(site.timezone)
    start = datetime.combine(report_date, shift.start, tzinfo=tz)
    end_date = report_date + timedelta(days=1) if shift.crosses_midnight else report_date
    end = datetime.combine(end_date, shift.end, tzinfo=tz)
    return start, end


def shifts_for_date(site: Site, report_date: date) -> list[Shift]:
    """Quarts actifs à cette date, selon leur jour de démarrage."""
    return [shift for shift in site.shifts if report_date.weekday() in shift.weekdays]


def build_site_report(
    store: Store,
    config: Config,
    site: Site,
    shift: Shift,
    report_date: date,
) -> SiteReport:
    """Construit le rapport d'un quart à partir des échantillons persistés."""
    start_local, end_local = shift_window(site, shift, report_date)
    start_ts = int(start_local.timestamp())
    end_ts = int(end_local.timestamp())
    interval = config.sample_interval_seconds

    duration_seconds = end_ts - start_ts
    expected_samples = max(1, duration_seconds // interval)

    samples = store.samples_between(site.id, start_ts, end_ts)
    by_zone: dict[str, list[Sample]] = {}
    for sample in samples:
        by_zone.setdefault(sample.zone, []).append(sample)

    tz = ZoneInfo(site.timezone)
    zone_reports = [
        _build_zone_report(
            zone=zone,
            samples=sorted(by_zone.get(zone.id, []), key=lambda s: s.ts),
            expected_samples=expected_samples,
            interval=interval,
            tz=tz,
        )
        for _camera, zone in site.zones()
    ]

    return SiteReport(
        site_id=site.id,
        site_label=site.label,
        report_date=report_date,
        shift_id=shift.id,
        shift_label=shift.label,
        window_start_local=start_local.strftime("%H:%M"),
        window_end_local=end_local.strftime("%H:%M"),
        timezone=site.timezone,
        sample_interval_seconds=interval,
        zones=tuple(zone_reports),
        collection_errors=tuple(store.errors_between(site.id, start_ts, end_ts)),
    )


def _build_zone_report(
    zone: Zone,
    samples: list[Sample],
    expected_samples: int,
    interval: int,
    tz: ZoneInfo,
) -> ZoneReport:
    occupied = 0
    fully_staffed = 0
    first_seen: int | None = None
    last_seen: int | None = None

    # Une série d'inoccupation ne doit être comptée que sur des échantillons
    # *consécutifs et réellement collectés*. Un trou dans les données interrompt
    # la série au lieu de la prolonger artificiellement.
    longest_idle_samples = 0
    current_idle_samples = 0
    previous_ts: int | None = None
    # Tolérance : un échantillon en retard de moins de 1,5 intervalle reste
    # considéré comme consécutif (dérive normale de la boucle de collecte).
    max_consecutive_gap = interval * 1.5

    for sample in samples:
        is_occupied = sample.person_count >= 1
        if is_occupied:
            occupied += 1
            if sample.person_count >= zone.expected_headcount:
                fully_staffed += 1
            if first_seen is None:
                first_seen = sample.ts
            last_seen = sample.ts
            current_idle_samples = 0
        else:
            contiguous = (
                previous_ts is not None and (sample.ts - previous_ts) <= max_consecutive_gap
            )
            current_idle_samples = current_idle_samples + 1 if contiguous else 1
            longest_idle_samples = max(longest_idle_samples, current_idle_samples)
        previous_ts = sample.ts

    received = len(samples)
    unoccupied_minutes = (received - occupied) * interval / 60.0

    return ZoneReport(
        zone_id=zone.id,
        label=zone.label,
        expected_headcount=zone.expected_headcount,
        max_idle_minutes=zone.max_idle_minutes,
        expected_samples=expected_samples,
        received_samples=received,
        occupied_samples=occupied,
        fully_staffed_samples=fully_staffed,
        unoccupied_minutes=round(unoccupied_minutes, 1),
        longest_idle_minutes=round(longest_idle_samples * interval / 60.0, 1),
        first_seen_local=(
            datetime.fromtimestamp(first_seen, tz).strftime("%H:%M")
            if first_seen is not None
            else None
        ),
        last_seen_local=(
            datetime.fromtimestamp(last_seen, tz).strftime("%H:%M")
            if last_seen is not None
            else None
        ),
    )


def build_reports(
    store: Store, config: Config, report_date: date, site_id: str | None = None
) -> list[SiteReport]:
    """Rapports de tous les quarts actifs à cette date, pour un site ou tous."""
    sites = [config.site(site_id)] if site_id else list(config.sites)
    reports: list[SiteReport] = []
    for site in sites:
        for shift in shifts_for_date(site, report_date):
            reports.append(build_site_report(store, config, site, shift, report_date))
    return reports


# --------------------------------------------------------------- présentation


def report_to_dict(report: SiteReport) -> dict:
    """Vue sérialisable, consommée par le générateur de PDF et les tests."""
    return {
        "site_id": report.site_id,
        "site_label": report.site_label,
        "date": report.report_date.isoformat(),
        "shift_id": report.shift_id,
        "shift_label": report.shift_label,
        "window": f"{report.window_start_local}–{report.window_end_local}",
        "timezone": report.timezone,
        "sample_interval_seconds": report.sample_interval_seconds,
        "overall_occupancy_rate": round(report.overall_occupancy_rate, 4),
        "zones": [
            {
                "zone_id": zone.zone_id,
                "label": zone.label,
                "expected_headcount": zone.expected_headcount,
                "occupancy_rate": round(zone.occupancy_rate, 4),
                "fully_staffed_rate": round(zone.fully_staffed_rate, 4),
                "unoccupied_minutes": zone.unoccupied_minutes,
                "longest_idle_minutes": zone.longest_idle_minutes,
                "first_seen": zone.first_seen_local,
                "last_seen": zone.last_seen_local,
                "coverage": round(zone.coverage, 4),
                "reliable": zone.is_reliable,
                "alert": zone.breached_idle_threshold,
            }
            for zone in report.zones
        ],
        "alerts": [zone.label for zone in report.zones_with_alerts],
        "data_gaps": [
            f"{zone.label}: {zone.coverage:.0%} des mesures collectées"
            for zone in report.unreliable_zones
        ],
        "collection_errors": [
            {"camera": camera, "message": message, "count": count}
            for camera, message, count in report.collection_errors
        ],
    }


def whatsapp_summary(report: SiteReport) -> str:
    """Résumé court, non nominatif, destiné au corps du message WhatsApp.

    Volontairement agrégé : le message transite par les serveurs Meta, hors
    d'Algérie. Aucun nom, aucun identifiant d'employé. Le détail par poste reste
    dans le PDF joint, et les noms — s'il y en a — restent sur site.
    """
    if not report.has_data:
        return (
            f"{report.site_label} — {report.shift_label} : aucune mesure collectée "
            f"sur la plage {report.window_start_local}–{report.window_end_local}. "
            f"Vérifier la liaison caméras."
        )

    lines = [
        f"{report.site_label} — {report.shift_label} "
        f"({report.window_start_local}–{report.window_end_local})",
        f"Occupation moyenne des postes : {report.overall_occupancy_rate:.0%}",
    ]

    alerts = report.zones_with_alerts
    if alerts:
        detail = ", ".join(
            f"{zone.label} ({zone.longest_idle_minutes:.0f} min)" for zone in alerts[:4]
        )
        suffix = f" +{len(alerts) - 4} autre(s)" if len(alerts) > 4 else ""
        lines.append(f"{len(alerts)} poste(s) au-delà du seuil d'inoccupation : {detail}{suffix}")
    else:
        lines.append("Aucun poste au-delà de son seuil d'inoccupation.")

    unreliable = report.unreliable_zones
    if unreliable:
        lines.append(
            f"Données partielles sur {len(unreliable)} poste(s) — "
            f"chiffres à lire avec réserve."
        )

    return "\n".join(lines)
