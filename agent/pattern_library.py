from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_PATTERNS: List[Dict[str, Any]] = [
    {"name": "ORA-12170", "category": "Database failure", "contains_any": ["ORA-12170"]},
    {"name": "ORA-12541", "category": "Database failure", "contains_any": ["ORA-12541"]},
    {"name": "DefaultConsumerBean", "category": "Integration Server failure", "contains_any": ["DefaultConsumerBean", "JMSException", "EJBException"]},
    {"name": "Transaction rolled back", "category": "Projection/API failure", "contains_any": ["Transaction rolled back"]},
    {"name": "HTTP 502/503", "category": "Ingress/gateway issue", "contains_any": ["HTTP 502", "HTTP 503", "upstream connect error"]},
    {"name": "OOMKilled", "category": "Memory exhaustion", "contains_any": ["OOMKilled", "OutOfMemoryError"]},
    {"name": "CrashLoopBackOff", "category": "Kubernetes pod crash", "contains_any": ["CrashLoopBackOff", "Back-off restarting failed container"]},
    {"name": "ImagePullBackOff", "category": "Deployment failure", "contains_any": ["ImagePullBackOff", "ErrImagePull"]},
    {"name": "FailedScheduling", "category": "Autoscaler/resource issue", "contains_any": ["FailedScheduling", "DiskPressure", "MemoryPressure"]},
    {"name": "Probe failures", "category": "Kubernetes pod crash", "contains_any": ["liveness probe failed", "readiness probe failed"]},
    {"name": "TLS handshake failed", "category": "Linkerd/service mesh issue", "contains_any": ["TLS handshake failed"]},
    {"name": "timeout/connection refused", "category": "Network/Connectivity issue", "contains_any": ["timeout", "connection refused"]},
]


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
    if not path.exists():
        return list(DEFAULT_PATTERNS)

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
