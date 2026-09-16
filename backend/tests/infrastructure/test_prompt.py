from pairo.domain.diff import AddedLine
from pairo.domain.finding import Axis, Finding, Source
from pairo.domain.ports import FileDiff
from pairo.infrastructure.llm.prompt import build_prompt


def test_includes_file_content() -> None:
    files = [FileDiff("app.py", [AddedLine(1, "x = 1")])]
    prompt = build_prompt(files, [], ["crafts"], "fr")
    assert "app.py" in prompt
    assert "x = 1" in prompt


def test_includes_requested_axes() -> None:
    files = [FileDiff("app.py", [AddedLine(1, "x = 1")])]
    prompt = build_prompt(files, [], ["crafts", "eco"], "fr")
    assert "crafts" in prompt
    assert "eco" in prompt
    assert "a11y" not in prompt


def test_mentions_existing_findings() -> None:
    files = [FileDiff("app.py", [AddedLine(1, "x = 1")])]
    existing = [
        Finding(
            axis=Axis.A11Y,
            file="app.py",
            line=1,
            issue="missing alt",
            suggestion="add alt",
            source=Source.RULE,
        )
    ]
    prompt = build_prompt(files, existing, ["a11y"], "fr")
    assert "missing alt" in prompt


def test_empty_files_still_produces_prompt() -> None:
    prompt = build_prompt([], [], ["crafts"], "fr")
    assert len(prompt) > 0


def test_multiple_files() -> None:
    files = [
        FileDiff("a.py", [AddedLine(1, "a = 1")]),
        FileDiff("b.py", [AddedLine(2, "b = 2")]),
    ]
    prompt = build_prompt(files, [], ["crafts"], "fr")
    assert "a.py" in prompt
    assert "b.py" in prompt


def test_output_format_instruction() -> None:
    files = [FileDiff("app.py", [AddedLine(1, "x = 1")])]
    prompt = build_prompt(files, [], ["crafts"], "fr")
    assert "JSON" in prompt
