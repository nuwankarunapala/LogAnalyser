from datetime import datetime

from agent.event_model import Event
from agent.root_cause_engine import score_root_causes


def test_root_cause_scoring_orders_highest_score_first() -> None:
    events = [
        Event(datetime.now(), "a", "pod_log", "svc-a", "error", "ORA-12170", "ORA-12170", "Database failure", "", 1),
        Event(datetime.now(), "b", "ingress_log", "svc-b", "warn", "HTTP 502", "HTTP 502/503", "Ingress/gateway issue", "", 1),
        Event(datetime.now(), "c", "pod_log", "svc-a", "error", "ORA-12170", "ORA-12170", "Database failure", "", 1),
    ]

    ranked = score_root_causes(events)
    assert ranked[0]["category"] == "Database failure"
    assert ranked[0]["confidence"] >= ranked[1]["confidence"]
