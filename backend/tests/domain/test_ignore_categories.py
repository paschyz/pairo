"""Tests for ignore_categories config and category-based filtering."""

from pairo.domain.finding import Axis, Finding, Source
from pairo.domain.repo_config import RepoConfig, parse_repo_config


def _finding(axis: str = "crafts", category: str = "naming") -> Finding:
    return Finding(
        axis=Axis(axis),
        file="app.py",
        line=1,
        issue="test",
        suggestion="fix",
        source=Source.LLM,
        category=category,
    )


class TestIgnoreCategories:
    def test_exact_match(self):
        config = RepoConfig(ignore_categories=["crafts.naming"])
        assert config.should_ignore_category("crafts", "naming") is True
        assert config.should_ignore_category("crafts", "complexity") is False

    def test_wildcard_axis(self):
        config = RepoConfig(ignore_categories=["crafts.*"])
        assert config.should_ignore_category("crafts", "naming") is True
        assert config.should_ignore_category("crafts", "complexity") is True
        assert config.should_ignore_category("eco", "n-plus-one") is False

    def test_empty_list_ignores_nothing(self):
        config = RepoConfig(ignore_categories=[])
        assert config.should_ignore_category("crafts", "naming") is False

    def test_multiple_patterns(self):
        config = RepoConfig(
            ignore_categories=["crafts.naming", "eco.*"]
        )
        assert config.should_ignore_category("crafts", "naming") is True
        assert config.should_ignore_category("eco", "n-plus-one") is True
        assert config.should_ignore_category("a11y", "img-alt") is False

    def test_parse_config_with_ignore_categories(self):
        raw = """
axes: [crafts]
ignore_categories: ["crafts.naming", "eco.*"]
"""
        config = parse_repo_config(raw)
        assert config.ignore_categories == ["crafts.naming", "eco.*"]

    def test_parse_config_default_empty(self):
        config = parse_repo_config(None)
        assert config.ignore_categories == []


class TestSuggestPersistentRule:
    def test_suggestion_text(self):
        from pairo.domain.filter_findings import suggest_persistent_rule

        text = suggest_persistent_rule("crafts.naming", 3)
        assert "crafts.naming" in text
        assert ".pairo.yml" in text
        assert "ignore_categories" in text
        assert "3 PR" in text

    def test_no_suggestion_below_threshold(self):
        from pairo.domain.filter_findings import suggest_persistent_rule

        assert suggest_persistent_rule("crafts.naming", 2) == ""
