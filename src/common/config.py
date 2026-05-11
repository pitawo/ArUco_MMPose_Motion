from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError(
            "PyYAML is required to read .yaml/.yml configs. Install pyyaml or use .json config."
        ) from exc

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("Config must be a mapping (YAML dictionary).")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Config must be a mapping (JSON object).")
    return data


def load_config(path: str | Path, required_keys: Iterable[str] | None = None) -> dict[str, Any]:
    """Load a YAML or JSON config file and validate required top-level keys."""
    config_path = Path(path)
    suffix = config_path.suffix.lower()

    if suffix in {".yaml", ".yml"}:
        config = _load_yaml(config_path)
    elif suffix == ".json":
        config = _load_json(config_path)
    else:
        raise ValueError("Unsupported config format. Use .yaml/.yml or .json")

    if required_keys is not None:
        required_set = set(required_keys)
        missing = required_set.difference(config.keys())
        if missing:
            missing_keys = ", ".join(sorted(missing))
            raise KeyError(f"Missing required config keys: {missing_keys}")
    return config
