from __future__ import annotations

from datetime import datetime
from pathlib import Path


def make_run_timestamp() -> str:
    """Return a timestamp string suitable for output file names."""
    return datetime.now().strftime("%Y%m%d%H%M%S")


def append_timestamp_to_path(path: str, timestamp: str) -> str:
    """Insert ``_<timestamp>`` before a path suffix.

    Example: ``outputs/report.csv`` -> ``outputs/report_20260101120000.csv``
    """

    original = Path(path)
    return str(original.with_name(f"{original.stem}_{timestamp}{original.suffix}"))
