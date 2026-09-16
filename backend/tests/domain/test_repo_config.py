from pairo.domain.repo_config import RepoConfig, parse_repo_config


def test_defaults_when_no_content() -> None:
    cfg = parse_repo_config(None)
    assert cfg.axes == ["crafts", "eco", "a11y"]
    assert cfg.max_image_kb == 200
    assert cfg.ignore == []
    assert cfg.language == "fr"


def test_parse_valid_yaml() -> None:
    raw = """\
axes: [crafts, a11y]
max_image_kb: 100
ignore: ["docs/**", "*.generated.ts"]
language: en
"""
    cfg = parse_repo_config(raw)
    assert cfg.axes == ["crafts", "a11y"]
    assert cfg.max_image_kb == 100
    assert cfg.ignore == ["docs/**", "*.generated.ts"]
    assert cfg.language == "en"


def test_partial_yaml_uses_defaults() -> None:
    cfg = parse_repo_config("axes: [eco]")
    assert cfg.axes == ["eco"]
    assert cfg.max_image_kb == 200
    assert cfg.language == "fr"


def test_invalid_yaml_returns_defaults_with_error() -> None:
    cfg = parse_repo_config("{{invalid yaml][")
    assert cfg.axes == ["crafts", "eco", "a11y"]
    assert cfg.parse_error is not None


def test_empty_string_returns_defaults() -> None:
    cfg = parse_repo_config("")
    assert cfg.axes == ["crafts", "eco", "a11y"]


def test_should_ignore_matching_path() -> None:
    cfg = RepoConfig(ignore=["docs/**", "*.lock"])
    assert cfg.should_ignore("docs/api/readme.md") is True
    assert cfg.should_ignore("package-lock.json") is False
    assert cfg.should_ignore("yarn.lock") is True
    assert cfg.should_ignore("src/main.ts") is False
