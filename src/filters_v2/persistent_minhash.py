"""SQLite-backed, cross-shard MinHash/LSH index for P1-2 pipelines."""

from __future__ import annotations

import hashlib
import sqlite3
import time
from pathlib import Path

from .heuristics import jaccard
from .minhash_dedup import _shingles, _signature


class PersistentMinHashIndex:
    def __init__(
        self,
        path: Path,
        *,
        shingle_size: int = 3,
        permutations: int = 64,
        bands: int = 16,
        seed: int = 42,
    ) -> None:
        if permutations % bands:
            raise ValueError("permutations must divide evenly into bands")
        self.path, self.shingle_size, self.permutations, self.bands, self.seed = (
            path,
            shingle_size,
            permutations,
            bands,
            seed,
        )
        self.rows_per_band = permutations // bands
        self.profile = {
            "signature_seconds": 0.0,
            "candidate_query_seconds": 0.0,
            "sqlite_insert_seconds": 0.0,
            "jaccard_seconds": 0.0,
            "confirmed_comparisons": 0,
        }
        self.db = sqlite3.connect(path)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS documents "
            "(doc_id TEXT PRIMARY KEY, split TEXT NOT NULL, text_hash TEXT NOT NULL, "
            "shingles TEXT NOT NULL)"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS lsh_bands "
            "(band INTEGER NOT NULL, band_hash TEXT NOT NULL, doc_id TEXT NOT NULL, "
            "PRIMARY KEY(band, band_hash, doc_id))"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS clusters "
            "(doc_id TEXT PRIMARY KEY, representative TEXT NOT NULL)"
        )
        identity = hashlib.sha256(
            f"{shingle_size}:{permutations}:{bands}:{seed}".encode()
        ).hexdigest()
        previous = self.db.execute("SELECT value FROM metadata WHERE key='identity'").fetchone()
        if previous and previous[0] != identity:
            raise ValueError("MinHash index configuration mismatch")
        self.db.execute("INSERT OR REPLACE INTO metadata VALUES ('identity',?)", (identity,))
        self.db.commit()

    def _prepare(self, text: str) -> tuple[set[str], tuple[int, ...], tuple[str, ...]]:
        started = time.perf_counter()
        shingles = _shingles(text, self.shingle_size)
        signature = _signature(shingles, self.permutations, self.seed)
        band_hashes = tuple(
            hashlib.sha256(
                repr(
                    signature[band * self.rows_per_band : (band + 1) * self.rows_per_band]
                ).encode()
            ).hexdigest()
            for band in range(self.bands)
        )
        self.profile["signature_seconds"] += time.perf_counter() - started
        return shingles, signature, band_hashes

    def _candidate_ids(self, band_hashes: tuple[str, ...]) -> set[str]:
        started = time.perf_counter()
        candidates: set[str] = set()
        for band, band_hash in enumerate(band_hashes):
            candidates.update(
                row[0]
                for row in self.db.execute(
                    "SELECT doc_id FROM lsh_bands WHERE band=? AND band_hash=?", (band, band_hash)
                )
            )
        self.profile["candidate_query_seconds"] += time.perf_counter() - started
        return candidates

    def candidates(self, text: str) -> tuple[set[str], set[str]]:
        shingles, _, band_hashes = self._prepare(text)
        return self._candidate_ids(band_hashes), shingles

    def add(self, doc_id: str, text: str, split: str) -> None:
        shingles, _, band_hashes = self._prepare(text)
        self._add_prepared(doc_id, text, split, shingles, band_hashes)

    def _add_prepared(
        self, doc_id: str, text: str, split: str, shingles: set[str], band_hashes: tuple[str, ...]
    ) -> None:
        started = time.perf_counter()
        self.db.execute(
            "INSERT OR IGNORE INTO documents VALUES (?,?,?,?)",
            (
                doc_id,
                split,
                hashlib.sha256(text.encode()).hexdigest(),
                "\u001f".join(sorted(shingles)),
            ),
        )
        self.db.executemany(
            "INSERT OR IGNORE INTO lsh_bands VALUES (?,?,?)",
            [(band, band_hash, doc_id) for band, band_hash in enumerate(band_hashes)],
        )
        self.db.execute("INSERT OR IGNORE INTO clusters VALUES (?,?)", (doc_id, doc_id))
        self.profile["sqlite_insert_seconds"] += time.perf_counter() - started

    def add_and_cluster(self, doc_id: str, text: str, split: str, *, threshold: float) -> str:
        """Persist a document and return its stable (lexicographically smallest) cluster ID.

        This is order-independent after ingestion: a later smaller ID replaces the
        representative of every connected candidate cluster in SQLite.
        """
        shingles, _, band_hashes = self._prepare(text)
        duplicates = self._confirmed_from_candidates(
            self._candidate_ids(band_hashes), shingles, threshold
        )
        representatives = [doc_id]
        for duplicate in duplicates:
            row = self.db.execute(
                "SELECT representative FROM clusters WHERE doc_id=?", (duplicate,)
            ).fetchone()
            representatives.append(str(row[0]) if row else duplicate)
        representative = min(representatives)
        self._add_prepared(doc_id, text, split, shingles, band_hashes)
        if duplicates:
            placeholders = ",".join("?" for _ in representatives)
            self.db.execute(
                f"UPDATE clusters SET representative=? WHERE representative IN ({placeholders})",
                (representative, *representatives),
            )
        self.db.execute(
            "UPDATE clusters SET representative=? WHERE doc_id=?", (representative, doc_id)
        )
        return representative

    def cluster_representatives(self) -> dict[str, str]:
        return {
            str(doc_id): str(representative)
            for doc_id, representative in self.db.execute(
                "SELECT doc_id, representative FROM clusters ORDER BY doc_id"
            )
        }

    def commit(self) -> None:
        self.db.commit()

    def confirmed_duplicates(self, text: str, threshold: float) -> list[str]:
        candidates, shingles = self.candidates(text)
        return self._confirmed_from_candidates(candidates, shingles, threshold)

    def _confirmed_from_candidates(
        self, candidates: set[str], shingles: set[str], threshold: float
    ) -> list[str]:
        confirmed: list[str] = []
        for doc_id in sorted(candidates):
            row = self.db.execute(
                "SELECT shingles FROM documents WHERE doc_id=?", (doc_id,)
            ).fetchone()
            started = time.perf_counter()
            self.profile["confirmed_comparisons"] += 1
            if row and jaccard(shingles, set(filter(None, row[0].split("\u001f")))) >= threshold:
                confirmed.append(doc_id)
            self.profile["jaccard_seconds"] += time.perf_counter() - started
        return confirmed

    def profile_snapshot(self) -> dict[str, float | int]:
        return dict(self.profile)

    def close(self) -> None:
        self.db.commit()
        self.db.close()
