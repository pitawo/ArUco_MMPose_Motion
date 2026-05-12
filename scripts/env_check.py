"""Environment / dependency version check.

主要パッケージのバージョンを表示し、不足があれば警告する。

Usage:
    python scripts/env_check.py
"""
from __future__ import annotations

import importlib
import sys


REQUIRED = [
    ("numpy", "1.26"),
    ("cv2", "4.10"),
    ("torch", "2.1"),
    ("mmpose", "1.3"),
    ("mmdet", None),
    ("mmcv", None),
    ("mmengine", None),
    ("yaml", None),
    ("pytest", None),
]


def _try_import_version(name: str) -> str | None:
    try:
        module = importlib.import_module(name)
    except ImportError:
        return None
    return getattr(module, "__version__", "unknown")


def main() -> int:
    print(f"Python: {sys.version.split()[0]}")
    print()
    print(f"{'Package':<12} {'Found':<14} {'Required':<10}")
    print("-" * 40)

    missing = []
    for name, expected in REQUIRED:
        version = _try_import_version(name)
        status = version if version else "NOT INSTALLED"
        print(f"{name:<12} {status:<14} {expected or '-':<10}")
        if version is None:
            missing.append(name)

    if missing:
        print()
        print(f"WARNING: Missing packages: {', '.join(missing)}")
        print("See docs/環境構築手順.md")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
