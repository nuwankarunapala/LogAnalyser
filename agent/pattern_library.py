from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def _load_yaml_optional(path: Path) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "YAML pattern file requested but PyYAML is not installed. "
            "Use the default JSON pattern library or install dependencies via `pip install -r requirements.txt`."
        ) from exc

    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid pattern library format: {path}")
    return payload


def load_pattern_library(path: Path) -> List[Dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
    elif suffix in {".yaml", ".yml"}:
        payload = _load_yaml_optional(path)
    else:
        raise ValueError(f"Unsupported pattern library extension for {path}; use .json, .yaml, or .yml")

    patterns = payload.get("patterns", []) if isinstance(payload, dict) else []
    if not isinstance(patterns, list):
        raise ValueError(f"Invalid pattern library format: {path}")
    return patterns
