import pytest

from pairo.domain.context_rule import (
    MAX_FILE_CHARS,
    MAX_RULE_CHARS,
    NO_RULE,
    RuleProposal,
    accept,
    is_trusted,
    merge_rule,
)


@pytest.mark.parametrize("assoc", ["OWNER", "MEMBER", "COLLABORATOR"])
def test_trusted_associations(assoc: str) -> None:
    assert is_trusted(assoc)


@pytest.mark.parametrize("assoc", ["CONTRIBUTOR", "NONE", "FIRST_TIMER", "", None])
def test_untrusted_associations(assoc: str | None) -> None:
    assert not is_trusted(assoc)


def test_no_rule_is_never_accepted() -> None:
    assert not accept(NO_RULE, 0.0)


def test_accept_refuses_persist_false() -> None:
    assert not accept(RuleProposal(False, 1.0, "Use Vue"), 0.7)


def test_accept_refuses_below_threshold() -> None:
    assert not accept(RuleProposal(True, 0.69, "Use Vue"), 0.7)


def test_accept_at_exact_threshold() -> None:
    assert accept(RuleProposal(True, 0.7, "Use Vue"), 0.7)


def test_accept_refuses_blank_rule() -> None:
    assert not accept(RuleProposal(True, 0.9, "  \n "), 0.7)


def test_merge_creates_file_with_header() -> None:
    assert merge_rule(None, "Use Vue") == "# Pairo context\n- Use Vue\n"


def test_merge_appends_to_existing() -> None:
    existing = "# Pairo context\n- Use Vue\n"
    assert merge_rule(existing, "No jQuery") == (
        "# Pairo context\n- Use Vue\n- No jQuery\n"
    )


def test_merge_appends_when_existing_has_no_trailing_newline() -> None:
    assert merge_rule("# Notes\n- A", "B") == "# Notes\n- A\n- B\n"


def test_merge_duplicate_ignores_case_and_spaces() -> None:
    assert merge_rule("# Pairo context\n- Use Vue\n", "  use   VUE ") is None


def test_merge_returns_none_when_file_would_overflow() -> None:
    assert merge_rule("x" * MAX_FILE_CHARS, "b") is None


def test_merge_flattens_multiline_rule() -> None:
    assert merge_rule(None, "a\n\nb") == "# Pairo context\n- a b\n"


def test_merge_truncates_long_rule() -> None:
    merged = merge_rule(None, "a" * 2000)
    assert merged == "# Pairo context\n- " + "a" * MAX_RULE_CHARS + "\n"
