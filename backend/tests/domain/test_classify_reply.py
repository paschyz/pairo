"""Tests for reply classification schema and batch classifier."""

from pairo.domain.classify_reply import (
    ReplyClassification,
    parse_classifications,
)


class TestReplyClassification:
    def test_rejects_high_confidence(self):
        c = ReplyClassification(
            fingerprint="fp1", verdict="rejects", confidence=0.9
        )
        assert c.is_rejection() is True

    def test_rejects_low_confidence_ignored(self):
        c = ReplyClassification(
            fingerprint="fp1", verdict="rejects", confidence=0.5
        )
        assert c.is_rejection() is False

    def test_accepts_not_rejection(self):
        c = ReplyClassification(
            fingerprint="fp1", verdict="accepts", confidence=0.95
        )
        assert c.is_rejection() is False

    def test_unclear_not_rejection(self):
        c = ReplyClassification(
            fingerprint="fp1", verdict="unclear", confidence=0.9
        )
        assert c.is_rejection() is False


class TestParseClassifications:
    def test_valid_json(self):
        raw = """[
            {"fingerprint": "fp1", "verdict": "rejects", "confidence": 0.92},
            {"fingerprint": "fp2", "verdict": "accepts", "confidence": 0.8}
        ]"""
        results = parse_classifications(raw)
        assert len(results) == 2
        assert results[0].fingerprint == "fp1"
        assert results[0].is_rejection() is True
        assert results[1].is_rejection() is False

    def test_invalid_json_returns_empty(self):
        assert parse_classifications("not json") == []

    def test_missing_fields_skipped(self):
        raw = '[{"fingerprint": "fp1"}]'
        assert parse_classifications(raw) == []

    def test_invalid_verdict_skipped(self):
        raw = '[{"fingerprint": "fp1", "verdict": "maybe", "confidence": 0.9}]'
        assert parse_classifications(raw) == []

    def test_empty_array(self):
        assert parse_classifications("[]") == []


class TestMemoryConfig:
    def test_default_classify_replies_false(self):
        from pairo.domain.repo_config import parse_repo_config

        config = parse_repo_config(None)
        assert config.memory_enabled is True
        assert config.memory_classify_replies is False

    def test_parse_memory_config(self):
        from pairo.domain.repo_config import parse_repo_config

        raw = """
memory:
  enabled: true
  classify_replies: true
"""
        config = parse_repo_config(raw)
        assert config.memory_enabled is True
        assert config.memory_classify_replies is True

    def test_memory_disabled(self):
        from pairo.domain.repo_config import parse_repo_config

        raw = """
memory:
  enabled: false
"""
        config = parse_repo_config(raw)
        assert config.memory_enabled is False
