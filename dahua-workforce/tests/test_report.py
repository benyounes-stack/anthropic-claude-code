"""Tests de l'agrégation de fin de journée.

Le point le plus important vérifié ici : un trou de données ne doit jamais être
présenté comme une absence au poste.
"""

from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

import pytest

from workforce.config import Camera, Config, Shift, Site, Zone
from workforce.report import (
    build_site_report,
    shift_window,
    shifts_for_date,
    whatsapp_summary,
)
from workforce.store import Sample, Store

TZ = ZoneInfo("Africa/Algiers")
INTERVAL = 15
REPORT_DATE = date(2026, 8, 12)  # un mercredi


def make_site(zones: list[Zone], shifts: list[Shift] | None = None) -> Site:
    camera = Camera(
        id="cam-01",
        host="192.168.1.10",
        username="u",
        password="p",
        zones=tuple(zones),
    )
    return Site(
        id="usine-01",
        label="Usine",
        cameras=(camera,),
        shifts=tuple(
            shifts
            or [
                Shift(
                    id="matin",
                    label="Quart du matin",
                    start=time(8, 0),
                    end=time(9, 0),
                    weekdays=(0, 1, 2, 3, 4),
                )
            ]
        ),
        timezone="Africa/Algiers",
    )


def make_config(site: Site) -> Config:
    return Config(sites=(site,), database_path=":memory:", sample_interval_seconds=INTERVAL)


def ts_at(hour: int, minute: int, second: int = 0) -> int:
    return int(datetime(2026, 8, 12, hour, minute, second, tzinfo=TZ).timestamp())


@pytest.fixture
def store():
    with Store(":memory:") as instance:
        yield instance


class TestShiftWindow:
    def test_day_shift(self):
        site = make_site([_zone("poste-01")])
        start, end = shift_window(site, site.shifts[0], REPORT_DATE)
        assert start.hour == 8 and end.hour == 9
        assert start.date() == end.date() == REPORT_DATE

    def test_night_shift_ends_next_day(self):
        night = Shift(id="nuit", label="Nuit", start=time(23, 0), end=time(7, 0))
        site = make_site([_zone("poste-01")], shifts=[night])
        start, end = shift_window(site, night, REPORT_DATE)
        assert start.date() == REPORT_DATE
        assert end.date() == date(2026, 8, 13)
        assert (end - start).total_seconds() == 8 * 3600

    def test_shifts_filtered_by_weekday(self):
        # Semaine ouvrable algérienne : dimanche (6) → jeudi (3).
        shift = Shift(id="matin", label="Matin", start=time(8, 0), end=time(16, 0),
                      weekdays=(6, 0, 1, 2, 3))
        site = make_site([_zone("poste-01")], shifts=[shift])
        assert shifts_for_date(site, date(2026, 8, 12)) == [shift]   # mercredi
        assert shifts_for_date(site, date(2026, 8, 14)) == []        # vendredi
        assert shifts_for_date(site, date(2026, 8, 16)) == [shift]   # dimanche


def _zone(zone_id: str, headcount: int = 1, max_idle: int = 15) -> Zone:
    return Zone(
        id=zone_id,
        label=f"Poste {zone_id[-1]}",
        polygon=((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)),
        expected_headcount=headcount,
        max_idle_minutes=max_idle,
    )


def _fill(store: Store, zone_id: str, counts: list[int], start_hour: int = 8) -> None:
    """Écrit une série d'échantillons contigus à partir de `start_hour:00`."""
    base = ts_at(start_hour, 0)
    store.record_samples(
        Sample(ts=base + index * INTERVAL, site="usine-01", zone=zone_id, person_count=count)
        for index, count in enumerate(counts)
    )


class TestOccupancy:
    def test_fully_occupied_zone(self, store):
        site = make_site([_zone("poste-01")])
        config = make_config(site)
        # 1 heure de quart / 15 s = 240 échantillons attendus.
        _fill(store, "poste-01", [1] * 240)

        report = build_site_report(store, config, site, site.shifts[0], REPORT_DATE)
        zone = report.zones[0]
        assert zone.received_samples == 240
        assert zone.occupancy_rate == 1.0
        assert zone.coverage == pytest.approx(1.0)
        assert zone.unoccupied_minutes == 0.0
        assert zone.longest_idle_minutes == 0.0
        assert not zone.breached_idle_threshold
        assert zone.is_reliable

    def test_idle_run_is_measured_in_minutes(self, store):
        site = make_site([_zone("poste-01", max_idle=15)])
        config = make_config(site)
        # 80 échantillons vides consécutifs × 15 s = 20 minutes d'absence.
        _fill(store, "poste-01", [1] * 80 + [0] * 80 + [1] * 80)

        report = build_site_report(store, config, site, site.shifts[0], REPORT_DATE)
        zone = report.zones[0]
        assert zone.longest_idle_minutes == pytest.approx(20.0)
        assert zone.unoccupied_minutes == pytest.approx(20.0)
        assert zone.occupancy_rate == pytest.approx(160 / 240)
        assert zone.breached_idle_threshold  # 20 min > seuil de 15 min

    def test_data_gap_does_not_extend_an_idle_run(self, store):
        """Le cœur de la règle d'honnêteté.

        Deux séries vides de 4 échantillons (1 min chacune) séparées par un trou
        de collecte de 30 minutes. La plus longue absence *mesurée* est de 1 min,
        pas de 31 : le trou n'est pas une absence.
        """
        site = make_site([_zone("poste-01", max_idle=15)])
        config = make_config(site)
        base = ts_at(8, 0)
        samples = [
            Sample(ts=base + index * INTERVAL, site="usine-01", zone="poste-01", person_count=0)
            for index in range(4)
        ]
        resume = base + 30 * 60
        samples += [
            Sample(ts=resume + index * INTERVAL, site="usine-01", zone="poste-01", person_count=0)
            for index in range(4)
        ]
        store.record_samples(samples)

        report = build_site_report(store, config, site, site.shifts[0], REPORT_DATE)
        zone = report.zones[0]
        assert zone.longest_idle_minutes == pytest.approx(1.0)
        assert not zone.breached_idle_threshold
        # Et la couverture chute, ce qui signale que le relevé est incomplet.
        assert zone.received_samples == 8
        assert not zone.is_reliable

    def test_zone_without_any_sample_is_not_reported_as_empty(self, store):
        site = make_site([_zone("poste-01")])
        config = make_config(site)

        report = build_site_report(store, config, site, site.shifts[0], REPORT_DATE)
        zone = report.zones[0]
        assert zone.received_samples == 0
        assert zone.coverage == 0.0
        assert not zone.is_reliable
        # Aucune absence n'est imputée à un poste qu'on n'a pas mesuré.
        assert zone.unoccupied_minutes == 0.0
        assert zone.longest_idle_minutes == 0.0
        assert not report.has_data

    def test_fully_staffed_rate_tracks_expected_headcount(self, store):
        site = make_site([_zone("poste-02", headcount=2)])
        config = make_config(site)
        # 120 échantillons à 2 personnes, 120 à une seule.
        _fill(store, "poste-02", [2] * 120 + [1] * 120)

        report = build_site_report(store, config, site, site.shifts[0], REPORT_DATE)
        zone = report.zones[0]
        assert zone.occupancy_rate == pytest.approx(1.0)      # poste tenu en continu
        assert zone.fully_staffed_rate == pytest.approx(0.5)  # mais à moitié en sous-effectif

    def test_first_and_last_presence(self, store):
        site = make_site([_zone("poste-01")])
        config = make_config(site)
        _fill(store, "poste-01", [0] * 40 + [1] * 160 + [0] * 40)

        report = build_site_report(store, config, site, site.shifts[0], REPORT_DATE)
        zone = report.zones[0]
        assert zone.first_seen_local == "08:10"  # 40 × 15 s = 10 min après 08:00
        assert zone.last_seen_local == "08:49"   # dernier échantillon occupé

    def test_samples_outside_the_window_are_excluded(self, store):
        site = make_site([_zone("poste-01")])
        config = make_config(site)
        store.record_samples(
            [
                Sample(ts=ts_at(7, 0), site="usine-01", zone="poste-01", person_count=1),
                Sample(ts=ts_at(8, 30), site="usine-01", zone="poste-01", person_count=1),
                Sample(ts=ts_at(10, 0), site="usine-01", zone="poste-01", person_count=1),
            ]
        )
        report = build_site_report(store, config, site, site.shifts[0], REPORT_DATE)
        assert report.zones[0].received_samples == 1


class TestSiteAggregation:
    def test_overall_rate_weighted_by_sample_count(self, store):
        site = make_site([_zone("poste-01"), _zone("poste-02")])
        config = make_config(site)
        _fill(store, "poste-01", [1] * 240)
        _fill(store, "poste-02", [0] * 240)

        report = build_site_report(store, config, site, site.shifts[0], REPORT_DATE)
        assert report.overall_occupancy_rate == pytest.approx(0.5)
        assert len(report.zones) == 2

    def test_alerts_collected(self, store):
        site = make_site([_zone("poste-01", max_idle=5), _zone("poste-02", max_idle=60)])
        config = make_config(site)
        _fill(store, "poste-01", [0] * 240)
        _fill(store, "poste-02", [0] * 240)

        report = build_site_report(store, config, site, site.shifts[0], REPORT_DATE)
        alert_ids = {zone.zone_id for zone in report.zones_with_alerts}
        # 60 min d'absence : dépasse le seuil de 5 min, pas celui de 60 min.
        assert alert_ids == {"poste-01"}

    def test_collection_errors_surface_in_the_report(self, store):
        site = make_site([_zone("poste-01")])
        config = make_config(site)
        store.record_error(ts_at(8, 5), "usine-01", "cam-01", "timeout")
        store.record_error(ts_at(8, 6), "usine-01", "cam-01", "timeout")

        report = build_site_report(store, config, site, site.shifts[0], REPORT_DATE)
        assert report.collection_errors == (("cam-01", "timeout", 2),)


class TestWhatsAppSummary:
    def test_summary_is_never_nominative(self, store):
        site = make_site([_zone("poste-01", max_idle=5)])
        config = make_config(site)
        _fill(store, "poste-01", [1] * 120 + [0] * 120)

        report = build_site_report(store, config, site, site.shifts[0], REPORT_DATE)
        summary = whatsapp_summary(report)
        assert "Usine" in summary
        assert "Poste 1" in summary
        assert "50 %" in summary or "50%" in summary
        # Le résumé ne parle que de postes : aucun champ identité n'existe en amont.
        assert "poste(s) au-delà du seuil" in summary

    def test_summary_flags_absent_data(self, store):
        site = make_site([_zone("poste-01")])
        config = make_config(site)

        report = build_site_report(store, config, site, site.shifts[0], REPORT_DATE)
        summary = whatsapp_summary(report)
        assert "aucune mesure collectée" in summary

    def test_summary_reports_clean_shift(self, store):
        site = make_site([_zone("poste-01", max_idle=30)])
        config = make_config(site)
        _fill(store, "poste-01", [1] * 240)

        report = build_site_report(store, config, site, site.shifts[0], REPORT_DATE)
        assert "Aucun poste au-delà" in whatsapp_summary(report)
