from dataclasses import replace

from pairo.domain.diff import AddedLine
from pairo.domain.finding import Axis, CodeSuggestion, Finding, Source
from pairo.domain.ports import FileDiff
from pairo.domain.suggestion import anchor_findings, sanitize_suggestions

FILES = [
    FileDiff(
        "a.py",
        [AddedLine(10, "x"), AddedLine(11, "y"), AddedLine(13, "z")],
    )
]


def test_anchor_keeps_findings_on_added_lines() -> None:
    f = _finding(10, None)
    assert anchor_findings([f], FILES) == [f]


def test_anchor_demotes_line_outside_the_diff_to_general_comment() -> None:
    off_line = _finding(12, CodeSuggestion("x"))
    off_file = _finding(10, None, file="ghost.py")
    a, b = anchor_findings([off_line, off_file], FILES)
    assert (a.line, a.code_suggestion) == (None, None)
    assert b.line is None


def test_anchor_leaves_general_findings_alone() -> None:
    f = _finding(None, None)
    assert anchor_findings([f], FILES) == [f]


def _finding(line: int | None, suggestion: CodeSuggestion | None, file: str = "a.py"):
    return Finding(
        axis=Axis.CRAFTS,
        file=file,
        line=line,
        issue="i",
        suggestion="s",
        source=Source.LLM,
        code_suggestion=suggestion,
    )


def test_no_code_suggestion_untouched() -> None:
    f = _finding(10, None)
    assert sanitize_suggestions([f], FILES) == ([f], 0)


def test_single_line_kept() -> None:
    f = _finding(10, CodeSuggestion("x2"))
    assert sanitize_suggestions([f], FILES) == ([f], 0)


def test_multi_line_kept() -> None:
    f = _finding(10, CodeSuggestion("a\nb", end_line=11))
    assert sanitize_suggestions([f], FILES) == ([f], 0)


def _dropped(f: Finding) -> None:
    out, dropped = sanitize_suggestions([f], FILES)
    assert dropped == 1
    assert out == [replace(f, code_suggestion=None)]


def test_empty_replacement_dropped() -> None:
    _dropped(_finding(10, CodeSuggestion("  \n")))


def test_line_outside_diff_dropped() -> None:
    _dropped(_finding(12, CodeSuggestion("x")))


def test_unknown_file_dropped() -> None:
    _dropped(_finding(10, CodeSuggestion("x"), file="other.py"))


def test_no_line_dropped() -> None:
    _dropped(_finding(None, CodeSuggestion("x")))


def test_inverted_range_dropped() -> None:
    _dropped(_finding(11, CodeSuggestion("x", end_line=10)))


def test_range_crossing_non_added_line_dropped() -> None:
    _dropped(_finding(11, CodeSuggestion("x", end_line=13)))


def test_oversized_replacement_dropped() -> None:
    _dropped(_finding(10, CodeSuggestion("\n".join(["l"] * 100))))
