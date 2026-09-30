from dataclasses import replace

from pairo.domain.diff import AddedLine
from pairo.domain.finding import Axis, CodeSuggestion, Finding, Source
from pairo.domain.ports import FileDiff
from pairo.domain.suggestion import sanitize_suggestions

FILES = [
    FileDiff(
        "a.py",
        [AddedLine(10, "x"), AddedLine(11, "y"), AddedLine(13, "z")],
    )
]


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
