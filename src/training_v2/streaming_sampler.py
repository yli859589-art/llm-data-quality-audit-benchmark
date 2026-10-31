"""Disk-backed, deterministic sampling for sharded training corpora."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator

from data.scalable_pipeline import iter_records, sha256_file


def _rank(seed: int, document_id: str) -> str:
    return hashlib.sha256(f"{seed}:{document_id}".encode("utf-8")).hexdigest()


class StreamingShardSampler:
    """Two-pass sampler that stores only durable metadata in SQLite.

    The document pool is fully scanned before selection.  Selection is based on
    a stable ID hash rather than file order, and text is read only in the second
    pass for selected rows.  This keeps corpus text out of RAM while retaining a
    reproducible pool definition for resume and audit.
    """

    def __init__(
        self,
        database: Path,
        *,
        shard_paths: tuple[str, ...],
        seed: int,
        tokenizer_name: str = "caller_supplied",
    ) -> None:
        self.database, self.shard_paths, self.seed, self.tokenizer_name = (
            database,
            shard_paths,
            seed,
            tokenizer_name,
        )
        self.db = sqlite3.connect(database)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS documents (doc_id TEXT PRIMARY KEY, shard INTEGER NOT NULL, ordinal INTEGER NOT NULL, tokens INTEGER NOT NULL, rank TEXT NOT NULL)"
        )

    def _identity(self) -> str:
        payload = {
            "shards": list(self.shard_paths),
            "hashes": [sha256_file(Path(path)) for path in self.shard_paths],
            "seed": self.seed,
            "tokenizer": self.tokenizer_name,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

    def build_index(self, token_count: Callable[[dict[str, Any]], int]) -> dict[str, int]:
        identity = self._identity()
        row = self.db.execute("SELECT value FROM metadata WHERE key='identity'").fetchone()
        if row and row[0] != identity:
            raise ValueError("sampler resume blocked: input shards, seed, or tokenizer changed")
        if row:
            total = self.db.execute(
                "SELECT COUNT(*), COALESCE(SUM(tokens), 0) FROM documents"
            ).fetchone()
            return {"documents": int(total[0]), "tokens": int(total[1]), "reused_index": 1}
        for shard_number, source_name in enumerate(self.shard_paths):
            for ordinal, row_data in enumerate(iter_records(Path(source_name))):
                doc_id = str(row_data.get("id", ""))
                tokens = int(token_count(row_data))
                if not doc_id or tokens <= 0:
                    continue
                self.db.execute(
                    "INSERT INTO documents VALUES (?,?,?,?,?)",
                    (doc_id, shard_number, ordinal, tokens, _rank(self.seed, doc_id)),
                )
        self.db.execute("INSERT INTO metadata VALUES ('identity',?)", (identity,))
        self.db.commit()
        total = self.db.execute(
            "SELECT COUNT(*), COALESCE(SUM(tokens), 0) FROM documents"
        ).fetchone()
        return {"documents": int(total[0]), "tokens": int(total[1]), "reused_index": 0}

    def select_ids(self, token_budget: int) -> list[str]:
        if token_budget <= 0:
            raise ValueError("token_budget must be positive")
        selected: list[str] = []
        used = 0
        for doc_id, tokens in self.db.execute(
            "SELECT doc_id, tokens FROM documents ORDER BY rank, doc_id"
        ):
            if used + int(tokens) <= token_budget:
                selected.append(str(doc_id))
                used += int(tokens)
        return selected

    def iter_selected_records(self, selected_ids: Iterable[str]) -> Iterator[dict[str, Any]]:
        wanted = set(selected_ids)
        for source_name in self.shard_paths:
            for row in iter_records(Path(source_name)):
                if str(row.get("id", "")) in wanted:
                    yield row

    def close(self) -> None:
        self.db.close()
