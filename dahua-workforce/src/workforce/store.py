"""Persistance des échantillons d'occupation (SQLite).

Ce qui est stocké : `(horodatage, site, zone, nombre de personnes)`.

Ce qui n'est **jamais** stocké : images, visages, gabarits biométriques,
identités. Le schéma ci-dessous est la garantie technique de cette promesse — il
n'a pas de colonne où une identité pourrait se glisser.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

_SCHEMA = """
CREATE TABLE IF NOT EXISTS samples (
    ts           INTEGER NOT NULL,   -- epoch en secondes, UTC
    site         TEXT    NOT NULL,
    zone         TEXT    NOT NULL,
    person_count INTEGER NOT NULL,
    PRIMARY KEY (ts, site, zone)
) WITHOUT ROWID;

CREATE INDEX IF NOT EXISTS idx_samples_site_ts ON samples (site, ts);

-- Les échecs de collecte sont tracés : un poste « vide » parce que la caméra
-- était injoignable ne doit jamais être présenté comme un poste inoccupé.
CREATE TABLE IF NOT EXISTS collection_errors (
    ts      INTEGER NOT NULL,
    site    TEXT    NOT NULL,
    camera  TEXT    NOT NULL,
    message TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_errors_site_ts ON collection_errors (site, ts);
"""


@dataclass(frozen=True)
class Sample:
    ts: int
    site: str
    zone: str
    person_count: int


class Store:
    """Accès SQLite. Utilisable comme gestionnaire de contexte."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(str(self.path), isolation_level=None)
        self._connection.row_factory = sqlite3.Row
        # WAL : le collecteur écrit en continu pendant que le rapport lit.
        if str(self.path) != ":memory:":
            self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=NORMAL")
        self._connection.executescript(_SCHEMA)

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        self._connection.execute("BEGIN")
        try:
            yield self._connection
        except Exception:
            self._connection.execute("ROLLBACK")
            raise
        else:
            self._connection.execute("COMMIT")

    # ------------------------------------------------------------- écritures

    def record_samples(self, samples: Iterable[Sample]) -> int:
        """Insère un lot d'échantillons. Un doublon (même ts/site/zone) écrase."""
        rows = [(s.ts, s.site, s.zone, s.person_count) for s in samples]
        if not rows:
            return 0
        with self._transaction() as connection:
            connection.executemany(
                "INSERT OR REPLACE INTO samples (ts, site, zone, person_count) "
                "VALUES (?, ?, ?, ?)",
                rows,
            )
        return len(rows)

    def record_error(self, ts: int, site: str, camera: str, message: str) -> None:
        with self._transaction() as connection:
            connection.execute(
                "INSERT INTO collection_errors (ts, site, camera, message) "
                "VALUES (?, ?, ?, ?)",
                (ts, site, camera, message[:500]),
            )

    def purge_before(self, cutoff_ts: int) -> int:
        """Supprime les données antérieures à `cutoff_ts`. Retourne le total effacé."""
        with self._transaction() as connection:
            samples = connection.execute(
                "DELETE FROM samples WHERE ts < ?", (cutoff_ts,)
            ).rowcount
            errors = connection.execute(
                "DELETE FROM collection_errors WHERE ts < ?", (cutoff_ts,)
            ).rowcount
        return samples + errors

    # ------------------------------------------------------------- lectures

    def samples_between(self, site: str, start_ts: int, end_ts: int) -> list[Sample]:
        """Échantillons d'un site sur `[start_ts, end_ts)`, ordonnés par temps."""
        rows = self._connection.execute(
            "SELECT ts, site, zone, person_count FROM samples "
            "WHERE site = ? AND ts >= ? AND ts < ? ORDER BY ts, zone",
            (site, start_ts, end_ts),
        ).fetchall()
        return [
            Sample(row["ts"], row["site"], row["zone"], row["person_count"])
            for row in rows
        ]

    def error_count_between(self, site: str, start_ts: int, end_ts: int) -> int:
        row = self._connection.execute(
            "SELECT COUNT(*) AS total FROM collection_errors "
            "WHERE site = ? AND ts >= ? AND ts < ?",
            (site, start_ts, end_ts),
        ).fetchone()
        return int(row["total"])

    def errors_between(
        self, site: str, start_ts: int, end_ts: int
    ) -> list[tuple[str, str, int]]:
        """Erreurs regroupées par (caméra, message), avec leur nombre d'occurrences."""
        rows = self._connection.execute(
            "SELECT camera, message, COUNT(*) AS total FROM collection_errors "
            "WHERE site = ? AND ts >= ? AND ts < ? "
            "GROUP BY camera, message ORDER BY total DESC",
            (site, start_ts, end_ts),
        ).fetchall()
        return [(row["camera"], row["message"], int(row["total"])) for row in rows]
