"""Tests de composition du rapport.

Vérifie que le HTML produit ne présente jamais une absence de mesure comme un
constat. C'est la règle d'honnêteté de la skill `custom-reports` appliquée au cas
qui compte ici : une caméra tombée ne doit pas produire un rapport qui affirme
« 0 % d'occupation » ou « aucun dépassement ».
"""

from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

import pytest

from workforce.config import Camera, Config, Shift, Site, Zone
from workforce.render import build_sections
from workforce.report import build_site_report
from workforce.store import Sample, Store

TZ = ZoneInfo("Africa/Algiers")
INTERVAL = 15
REPORT_DATE = date(2026, 8, 12)
SQUARE = ((0.0, 0.5), (1.0, 0.5), (1.0, 1.0), (0.0, 1.0))


def _make(zones: list[Zone]) -> tuple[Site, Config, Shift]:
    camera = Camera(
        id="cam-01", host="10.0.0.1", username="u", password="p", zones=tuple(zones)
    )
    shift = Shift(id="matin", label="Matin", start=time(8, 0), end=time(9, 0))
    site = Site(
        id="usine-01",
        label="Usine",
        cameras=(camera,),
        shifts=(shift,),
        timezone="Africa/Algiers",
    )
    config = Config(
        sites=(site,), database_path=":memory:", sample_interval_seconds=INTERVAL
    )
    return site, config, shift


def _zone(zone_id: str, label: str, max_idle: int = 15) -> Zone:
    return Zone(id=zone_id, label=label, polygon=SQUARE, max_idle_minutes=max_idle)


def _sections(store: Store, zones: list[Zone]) -> str:
    site, config, shift = _make(zones)
    report = build_site_report(store, config, site, shift, REPORT_DATE)
    return build_sections(report)


@pytest.fixture
def store():
    with Store(":memory:") as instance:
        yield instance


def _fill(store: Store, zone_id: str, counts: list[int]) -> None:
    base = int(datetime(2026, 8, 12, 8, 0, tzinfo=TZ).timestamp())
    store.record_samples(
        Sample(base + index * INTERVAL, "usine-01", zone_id, count)
        for index, count in enumerate(counts)
    )


class TestNoDataIsNotAVerdict:
    def test_no_data_never_claims_zero_occupancy(self, store):
        html = _sections(store, [_zone("poste-01", "Poste 1")])
        assert "Non mesuré" in html
        assert "aucune mesure sur la plage" in html
        # Le piège : afficher « 0 % » et le tag rouge « sous le seuil » revient à
        # conclure d'un vide de mesure.
        assert "Sous le seuil" not in html

    def test_no_data_never_claims_compliance(self, store):
        html = _sections(store, [_zone("poste-01", "Poste 1")])
        assert "rien à confirmer" in html
        assert "✅ Aucun dépassement" not in html
        assert "workforce probe" in html

    def test_no_data_does_not_repeat_the_partial_measure_note(self, store):
        html = _sections(store, [_zone("poste-01", "Poste 1")])
        assert "Mesure partielle" not in html


class TestPartialData:
    def test_clean_shift_flags_zones_excluded_from_the_claim(self, store):
        _fill(store, "poste-01", [1] * 240)
        html = _sections(
            store, [_zone("poste-01", "Poste 1"), _zone("poste-02", "Poste 2")]
        )
        # Poste 2 n'a aucune mesure : le « aucun dépassement » ne peut pas le couvrir.
        assert "Aucun dépassement" in html
        assert "Constat partiel" in html
        assert "Poste 2" in html

    def test_partial_coverage_is_labelled_in_the_table(self, store):
        _fill(store, "poste-01", [1] * 100)  # 100/240 échantillons
        html = _sections(store, [_zone("poste-01", "Poste 1")])
        assert "mesuré)" in html          # « 42 % mesuré » accolé au taux
        assert "Mesure partielle" in html


class TestMeasuredShift:
    def test_alert_is_reported_with_its_threshold(self, store):
        _fill(store, "poste-01", [1] * 60 + [0] * 120 + [1] * 60)
        html = _sections(store, [_zone("poste-01", "Poste 1", max_idle=10)])
        assert "Postes au-delà du seuil" in html
        assert "30 min" in html            # 120 × 15 s d'absence continue
        assert "seuil fixé à 10 min" in html

    def test_method_block_states_no_image_and_no_identification(self, store):
        _fill(store, "poste-01", [1] * 240)
        html = _sections(store, [_zone("poste-01", "Poste 1")])
        assert "Aucune image n'est conservée" in html
        assert "jamais « qui »" in html

    def test_payroll_limitation_always_present(self, store):
        _fill(store, "poste-01", [1] * 240)
        html = _sections(store, [_zone("poste-01", "Poste 1")])
        # Doit figurer dans chaque rapport, y compris les plus flatteurs.
        assert "pas des heures travaillées par personne" in html
        assert "terminal de pointage par badge" in html

    def test_zone_labels_are_escaped(self, store):
        _fill(store, "poste-01", [1] * 240)
        html = _sections(store, [_zone("poste-01", 'Poste "A" & <b>')])
        assert "&amp;" in html
        assert "<b>" not in html
