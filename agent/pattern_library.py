from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml


def load_pattern_library(path: Path) -> List[Dict[str, Any]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    patterns = payload.get("patterns", [])
    if not isinstance(patterns, list):
        raise ValueError(f"Invalid pattern library format: {path}")
    return patterns
