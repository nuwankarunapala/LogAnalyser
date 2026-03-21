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


def test_yaml_file_without_pyyaml_raises_clear_error(tmp_path: Path, monkeypatch) -> None:
    yaml_file = tmp_path / "patterns.yaml"
    yaml_file.write_text("patterns: []\n", encoding="utf-8")

    monkeypatch.setattr("importlib.util.find_spec", lambda name: None if name == "yaml" else object())

    try:
        load_pattern_library(yaml_file)
    except RuntimeError as exc:
        assert "PyYAML is not installed" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when PyYAML is unavailable for YAML patterns")
