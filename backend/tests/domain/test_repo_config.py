from pairo.domain.repo_config import RepoConfig, parse_repo_config


def test_defaults_when_no_content() -> None:
    cfg = parse_repo_config(None)
    assert cfg.axes == ["crafts", "eco", "a11y"]
    assert cfg.max_image_kb == 200
    assert cfg.ignore == []
    assert cfg.language == "en"


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
    assert cfg.language == "en"


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


def test_context_propose_rules_defaults_to_true() -> None:
    assert parse_repo_config(None).context_propose_rules is True
    assert parse_repo_config("axes: [crafts]\n").context_propose_rules is True


def test_context_propose_rules_can_be_disabled() -> None:
    cfg = parse_repo_config("context:\n  propose_rules: false\n")
    assert cfg.context_propose_rules is False


def test_context_section_not_a_mapping_falls_back_to_default() -> None:
    assert parse_repo_config("context: nope\n").context_propose_rules is True
