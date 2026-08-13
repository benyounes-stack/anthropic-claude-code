"""Tests de la persistance et du chargement de configuration."""

from __future__ import annotations

import textwrap

import pytest

from workforce.config import ConfigError, Zone, load_config
from workforce.dahua import parse_cgi_body
from workforce.store import Sample, Store


class TestStore:
    def test_schema_has_no_column_for_identity(self):
        """Garantie technique : aucune colonne ne peut accueillir une identité."""
        with Store(":memory:") as store:
            columns = {
                row[1]
                for row in store._connection.execute("PRAGMA table_info(samples)")
            }
        assert columns == {"ts", "site", "zone", "person_count"}

    def test_record_and_read_back(self):
        with Store(":memory:") as store:
            written = store.record_samples(
                [
                    Sample(ts=100, site="s", zone="z1", person_count=1),
                    Sample(ts=100, site="s", zone="z2", person_count=0),
                ]
            )
            assert written == 2
            samples = store.samples_between("s", 0, 200)
            assert [s.zone for s in samples] == ["z1", "z2"]

    def test_duplicate_sample_replaces(self):
        with Store(":memory:") as store:
            store.record_samples([Sample(ts=100, site="s", zone="z", person_count=1)])
            store.record_samples([Sample(ts=100, site="s", zone="z", person_count=3)])
            samples = store.samples_between("s", 0, 200)
            assert len(samples) == 1
            assert samples[0].person_count == 3

    def test_window_is_half_open(self):
        with Store(":memory:") as store:
            store.record_samples(
                [
                    Sample(ts=100, site="s", zone="z", person_count=1),
                    Sample(ts=200, site="s", zone="z", person_count=1),
                ]
            )
            # [100, 200) inclut 100, exclut 200 — évite le double comptage entre
            # deux quarts qui se touchent.
            assert len(store.samples_between("s", 100, 200)) == 1

    def test_sites_are_isolated(self):
        with Store(":memory:") as store:
            store.record_samples(
                [
                    Sample(ts=100, site="a", zone="z", person_count=1),
                    Sample(ts=100, site="b", zone="z", person_count=1),
                ]
            )
            assert len(store.samples_between("a", 0, 200)) == 1

    def test_purge_respects_cutoff(self):
        with Store(":memory:") as store:
            store.record_samples(
                [
                    Sample(ts=100, site="s", zone="z", person_count=1),
                    Sample(ts=500, site="s", zone="z", person_count=1),
                ]
            )
            store.record_error(100, "s", "cam", "vieux")
            removed = store.purge_before(400)
            assert removed == 2  # un échantillon + une erreur
            assert len(store.samples_between("s", 0, 1000)) == 1

    def test_errors_grouped_by_camera_and_message(self):
        with Store(":memory:") as store:
            store.record_error(10, "s", "cam-01", "timeout")
            store.record_error(20, "s", "cam-01", "timeout")
            store.record_error(30, "s", "cam-02", "401")
            grouped = dict(((cam, msg), n) for cam, msg, n in store.errors_between("s", 0, 100))
            assert grouped[("cam-01", "timeout")] == 2
            assert grouped[("cam-02", "401")] == 1


class TestZoneValidation:
    def test_polygon_needs_three_points(self):
        with pytest.raises(ConfigError, match="au moins 3 points"):
            Zone(id="z", label="Z", polygon=((0.0, 0.0), (1.0, 1.0)))

    def test_coordinates_must_be_normalised(self):
        # Erreur d'installation la plus probable : coller des pixels au lieu de
        # coordonnées normalisées.
        with pytest.raises(ConfigError, match="hors de"):
            Zone(id="z", label="Z", polygon=((0.0, 0.0), (1920.0, 0.0), (1920.0, 1080.0)))

    def test_headcount_must_be_positive(self):
        with pytest.raises(ConfigError, match="expected_headcount"):
            Zone(
                id="z",
                label="Z",
                polygon=((0.0, 0.0), (1.0, 0.0), (1.0, 1.0)),
                expected_headcount=0,
            )


_MINIMAL_YAML = """
sites:
  - id: usine-01
    label: Usine
    timezone: Africa/Algiers
    shifts:
      - id: matin
        label: Matin
        start: "07:00"
        end: "15:00"
        weekdays: [6, 0, 1, 2, 3]
    cameras:
      - id: cam-01
        host: 192.168.1.10
        username: workforce
        password: ${TEST_CAM_PASSWORD}
        zones:
          - id: poste-01
            label: Poste 1
            polygon: [[0.0, 0.5], [1.0, 0.5], [1.0, 1.0], [0.0, 1.0]]
"""


class TestLoadConfig:
    def test_loads_and_expands_environment(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TEST_CAM_PASSWORD", "s3cret")
        path = tmp_path / "sites.yaml"
        path.write_text(textwrap.dedent(_MINIMAL_YAML), encoding="utf-8")

        config = load_config(path)
        site = config.site("usine-01")
        assert site.cameras[0].password == "s3cret"
        assert site.shifts[0].weekdays == (6, 0, 1, 2, 3)
        assert len(site.zones()) == 1

    def test_missing_environment_variable_is_an_error(self, tmp_path, monkeypatch):
        monkeypatch.delenv("TEST_CAM_PASSWORD", raising=False)
        path = tmp_path / "sites.yaml"
        path.write_text(textwrap.dedent(_MINIMAL_YAML), encoding="utf-8")

        with pytest.raises(ConfigError, match="TEST_CAM_PASSWORD"):
            load_config(path)

    def test_names_default_to_privacy_safe_values(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TEST_CAM_PASSWORD", "s3cret")
        path = tmp_path / "sites.yaml"
        path.write_text(textwrap.dedent(_MINIMAL_YAML), encoding="utf-8")

        config = load_config(path)
        # Le transfert de noms hors d'Algérie doit rester un choix explicite.
        assert config.whatsapp.include_employee_names is False

    def test_duplicate_zone_id_across_cameras_rejected(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TEST_CAM_PASSWORD", "s3cret")
        # Une seconde caméra qui réutilise l'identifiant de zone `poste-01`.
        duplicated = textwrap.dedent(_MINIMAL_YAML).rstrip() + (
            "\n"
            "      - id: cam-02\n"
            "        host: 192.168.1.11\n"
            "        username: workforce\n"
            "        password: ${TEST_CAM_PASSWORD}\n"
            "        zones:\n"
            "          - id: poste-01\n"
            "            label: Poste 1 bis\n"
            "            polygon: [[0.0, 0.5], [1.0, 0.5], [1.0, 1.0], [0.0, 1.0]]\n"
        )
        path = tmp_path / "sites.yaml"
        path.write_text(duplicated, encoding="utf-8")

        with pytest.raises(ConfigError, match="dupliqué"):
            load_config(path)

    def test_aggressive_sample_interval_rejected(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TEST_CAM_PASSWORD", "s3cret")
        path = tmp_path / "sites.yaml"
        path.write_text(
            "sample_interval_seconds: 1\n" + textwrap.dedent(_MINIMAL_YAML),
            encoding="utf-8",
        )
        with pytest.raises(ConfigError, match="cadence trop agressive"):
            load_config(path)

    def test_site_without_shift_rejected(self, tmp_path):
        path = tmp_path / "sites.yaml"
        path.write_text(
            textwrap.dedent(
                """
                sites:
                  - id: usine-01
                    cameras:
                      - id: cam-01
                        host: 1.2.3.4
                        username: u
                        password: p
                        zones:
                          - id: poste-01
                            polygon: [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]]
                """
            ),
            encoding="utf-8",
        )
        with pytest.raises(ConfigError, match="aucun quart"):
            load_config(path)


class TestParseCgiBody:
    def test_parses_prefixed_keys_both_ways(self):
        parsed = parse_cgi_body("table.General.MachineName=cam-ligne-a\r\ntype=IPC-HDW1230\r\n")
        assert parsed["table.General.MachineName"] == "cam-ligne-a"
        assert parsed["MachineName"] == "cam-ligne-a"
        assert parsed["type"] == "IPC-HDW1230"

    def test_ignores_blank_and_malformed_lines(self):
        assert parse_cgi_body("\n\nnot-a-pair\nsn=ABC123\n") == {"sn": "ABC123"}

    def test_empty_body(self):
        assert parse_cgi_body("") == {}
