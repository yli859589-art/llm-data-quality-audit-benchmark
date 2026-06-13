from __future__ import annotations

import json
from pathlib import Path

from artifacts_v2.canonical_io import canonicalize_text_bytes, write_canonical_json, write_canonical_text


def test_canonical_text_normalizes_crlf_to_lf(tmp_path: Path) -> None:
    path = tmp_path / "sample.md"
    path.write_bytes(b"a\r\nb\r\n")
    canonicalize_text_bytes(path)
    assert path.read_bytes() == b"a\nb\n"


def test_canonical_json_uses_stable_key_order_and_final_lf(tmp_path: Path) -> None:
    path = tmp_path / "sample.json"
    write_canonical_json(path, {"b": 1, "a": 2})
    text = path.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert text.index('"a"') < text.index('"b"')
    assert json.loads(text) == {"a": 2, "b": 1}


def test_canonical_text_writer_final_newline(tmp_path: Path) -> None:
    path = tmp_path / "sample.txt"
    write_canonical_text(path, "hello\r\nworld")
    assert path.read_bytes() == b"hello\nworld\n"

