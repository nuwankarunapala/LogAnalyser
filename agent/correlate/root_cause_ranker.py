"""Root-cause ranking helpers."""

from __future__ import annotations

from typing import Any, Dict, List


def rank_root_causes(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rank root-cause candidates by severity score and match count."""
    return sorted(
        signals,
        key=lambda s: (s.get("severity_score", 0), s.get("match_count", 0)),
        reverse=True,
    )
