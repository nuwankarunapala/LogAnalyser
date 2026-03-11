from agent.parsers import parse_timestamp, match_pattern


def test_parse_timestamp_iso() -> None:
    ts = parse_timestamp("2026-03-01 10:15:00 ERROR boom")
    assert ts is not None
    assert ts.year == 2026 and ts.minute == 15


def test_pattern_detection() -> None:
    patterns = [{"name": "OOMKilled", "category": "Memory", "contains_any": ["OOMKilled"]}]
    name, category = match_pattern("pod terminated with OOMKilled", patterns)
    assert name == "OOMKilled"
    assert category == "Memory"
