from pairo.domain.diff import AddedLine
from pairo.domain.finding import Axis, Source
from pairo.domain.rules.alt import check_missing_alt


def test_img_without_alt() -> None:
    lines = [AddedLine(number=3, content='  <img src="logo.png">')]
    findings = check_missing_alt("App.vue", lines)
    assert len(findings) == 1
    assert findings[0].axis == Axis.A11Y
    assert findings[0].line == 3
    assert findings[0].source == Source.RULE


def test_img_with_alt_is_ok() -> None:
    lines = [AddedLine(number=1, content='<img src="x.png" alt="logo">')]
    assert check_missing_alt("App.vue", lines) == []


def test_img_with_empty_alt_is_ok() -> None:
    """Empty alt is valid for decorative images."""
    lines = [AddedLine(number=1, content='<img src="x.png" alt="">')]
    assert check_missing_alt("App.vue", lines) == []


def test_multiple_imgs_on_different_lines() -> None:
    lines = [
        AddedLine(number=5, content='<img src="a.png">'),
        AddedLine(number=6, content='<img src="b.png" alt="b">'),
        AddedLine(number=7, content='<img src="c.png">'),
    ]
    findings = check_missing_alt("page.html", lines)
    assert len(findings) == 2
    assert findings[0].line == 5
    assert findings[1].line == 7


def test_self_closing_img_without_alt() -> None:
    lines = [AddedLine(number=1, content='<img src="x.png" />')]
    assert len(check_missing_alt("App.tsx", lines)) == 1


def test_non_eligible_file_skipped() -> None:
    lines = [AddedLine(number=1, content='<img src="x.png">')]
    assert check_missing_alt("main.py", lines) == []


def test_eligible_extensions() -> None:
    line = [AddedLine(number=1, content='<img src="x.png">')]
    for ext in ("index.html", "App.jsx", "App.tsx", "App.vue"):
        assert len(check_missing_alt(ext, line)) == 1
