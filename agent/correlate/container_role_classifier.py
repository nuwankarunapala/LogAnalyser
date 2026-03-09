"""Container role classification for sidecar vs main workloads."""

from typing import Dict


def classify(container_name: str) -> str:
    """Classify container role using basic naming conventions."""
    name = container_name.lower()
    sidecar_keywords = ("sidecar", "proxy", "istio", "envoy")
    if any(k in name for k in sidecar_keywords):
        return "sidecar"
    return "main"
