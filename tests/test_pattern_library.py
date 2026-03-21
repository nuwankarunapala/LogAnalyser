from pathlib import Path

from agent.pattern_library import DEFAULT_PATTERNS, load_pattern_library


def test_load_pattern_library_from_json(tmp_path: Path) -> None:
    pattern_file = tmp_path / "patterns.json"
    pattern_file.write_text('{"patterns":[{"name":"x","category":"c","contains_any":["a"]}]}', encoding="utf-8")
    patterns = load_pattern_library(pattern_file)
    assert patterns[0]["name"] == "x"


def test_load_pattern_library_falls_back_when_file_missing(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist.json"
    patterns = load_pattern_library(missing)
    assert patterns == DEFAULT_PATTERNS
