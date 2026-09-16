from pairo.domain.finding import Axis, Source
from pairo.domain.rules.image_size import check_image_size


def test_oversized_image() -> None:
    findings = check_image_size("assets/hero.png", size_kb=350, max_kb=200)
    assert len(findings) == 1
    assert findings[0].axis == Axis.ECO
    assert findings[0].line is None
    assert findings[0].source == Source.RULE
    assert "350" in findings[0].issue
    assert "200" in findings[0].issue


def test_image_within_limit() -> None:
    assert check_image_size("logo.png", size_kb=150, max_kb=200) == []


def test_image_exactly_at_limit() -> None:
    assert check_image_size("icon.svg", size_kb=200, max_kb=200) == []


def test_non_image_file_skipped() -> None:
    assert check_image_size("main.py", size_kb=500, max_kb=200) == []


def test_eligible_extensions() -> None:
    for ext in ("a.png", "b.jpg", "c.jpeg", "d.gif", "e.svg", "f.webp", "g.avif"):
        findings = check_image_size(ext, size_kb=300, max_kb=200)
        assert len(findings) == 1, f"Expected finding for {ext}"
