from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class Event:
    timestamp: Optional[datetime]
    source_file: str
    source_type: str
    component: str
    severity: str
    message: str
    matched_pattern: Optional[str] = None
    category: str = "unknown"
    raw_line: str = ""
    line_no: int = 0

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["timestamp"] = self.timestamp.isoformat() if self.timestamp else None
        return payload
