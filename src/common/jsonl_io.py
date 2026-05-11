from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Read an entire JSONL file into a list of dicts."""
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            rows.append(json.loads(stripped))
    return rows


def iter_jsonl(path: str | Path) -> Iterator[dict[str, Any]]:
    """Stream a JSONL file line-by-line (avoids loading the whole file into memory)."""
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            yield json.loads(stripped)
