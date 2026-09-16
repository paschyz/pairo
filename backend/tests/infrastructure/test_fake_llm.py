from pairo.domain.diff import AddedLine
from pairo.domain.finding import Axis, Source
from pairo.domain.ports import FileDiff
from pairo.infrastructure.llm.fake import FakeLLMReviewer


async def test_fake_returns_one_finding_per_file() -> None:
    reviewer = FakeLLMReviewer()
    files = [
        FileDiff("src/main.py", [AddedLine(1, "x = 1")]),
        FileDiff("src/util.py", [AddedLine(5, "y = 2")]),
    ]
    findings = await reviewer.review(files, [], ["crafts"], "fr")
    assert len(findings) == 2
    assert all(f.source == Source.LLM for f in findings)
    assert all(f.axis == Axis.CRAFTS for f in findings)


async def test_fake_returns_empty_for_no_files() -> None:
    reviewer = FakeLLMReviewer()
    findings = await reviewer.review([], [], ["crafts", "eco"], "fr")
    assert findings == []


async def test_fake_skips_files_with_no_added_lines() -> None:
    reviewer = FakeLLMReviewer()
    files = [FileDiff("empty.py", [])]
    findings = await reviewer.review(files, [], ["crafts"], "fr")
    assert findings == []
