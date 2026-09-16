import pytest

from pairo.domain.marker import build_marker, parse_marker


class TestBuildMarker:
    def test_basic_marker(self):
        m = build_marker(fingerprint="abc123def456", axis="crafts", category="naming")
        assert "<!-- pairo:" in m
        assert "fp=abc123def456" in m
        assert "axis=crafts" in m
        assert "cat=naming" in m
        assert "v=1" in m
        assert m.endswith(" -->")

    def test_marker_is_single_line(self):
        m = build_marker("abc123", "eco", "image-size")
        assert "\n" not in m


class TestParseMarker:
    def test_round_trip(self):
        m = build_marker("abc123def456", "crafts", "naming")
        text = f"Some review comment\n\n{m}"
        result = parse_marker(text)
        assert result is not None
        assert result["fp"] == "abc123def456"
        assert result["axis"] == "crafts"
        assert result["cat"] == "naming"
        assert result["v"] == "1"

    def test_no_marker_returns_none(self):
        assert parse_marker("Just a regular comment") is None

    def test_malformed_marker_returns_none(self):
        assert parse_marker("<!-- pairo:garbage -->") is None

    def test_partial_marker_returns_none(self):
        # Missing required fields
        assert parse_marker("<!-- pairo:fp=abc;v=1 -->") is None

    def test_marker_embedded_in_longer_text(self):
        text = (
            "This is a finding.\n\nPlease fix.\n\n"
            "<!-- pairo:fp=deadbeef12345678;axis=a11y;cat=img-alt;v=1 -->"
        )
        result = parse_marker(text)
        assert result is not None
        assert result["fp"] == "deadbeef12345678"

    def test_empty_string(self):
        assert parse_marker("") is None

    def test_tolerant_of_extra_fields(self):
        text = "<!-- pairo:fp=abc;axis=eco;cat=size;v=1;extra=ok -->"
        result = parse_marker(text)
        assert result is not None
        assert result["fp"] == "abc"
