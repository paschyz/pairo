"""Tests for @pairo command parsing."""

from pairo.domain.command import parse_command


class TestParseCommand:
    def test_ignore_bare(self):
        cmd = parse_command("@pairo ignore")
        assert cmd is not None
        assert cmd.action == "ignore"
        assert cmd.reason is None

    def test_ignore_with_reason(self):
        cmd = parse_command("@pairo ignore not relevant to our codebase")
        assert cmd is not None
        assert cmd.action == "ignore"
        assert cmd.reason == "not relevant to our codebase"

    def test_valid(self):
        cmd = parse_command("@pairo valid")
        assert cmd is not None
        assert cmd.action == "valid"
        assert cmd.reason is None

    def test_case_insensitive(self):
        assert parse_command("@Pairo Ignore")  is not None
        assert parse_command("@PAIRO VALID") is not None

    def test_embedded_in_text(self):
        cmd = parse_command("I disagree, @pairo ignore this is fine")
        assert cmd is not None
        assert cmd.action == "ignore"
        assert cmd.reason == "this is fine"

    def test_no_command(self):
        assert parse_command("This is just a regular comment") is None

    def test_pairo_without_command(self):
        assert parse_command("@pairo what do you think?") is None

    def test_empty(self):
        assert parse_command("") is None

    def test_multiline_command_in_first_matching_line(self):
        text = "Some context\n@pairo ignore legacy code\nMore text"
        cmd = parse_command(text)
        assert cmd is not None
        assert cmd.reason == "legacy code"
