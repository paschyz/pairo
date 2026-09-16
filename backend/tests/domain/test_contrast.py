import pytest

from pairo.domain.diff import AddedLine
from pairo.domain.finding import Axis, Source
from pairo.domain.rules.contrast import (
    check_contrast,
    contrast_ratio,
    relative_luminance,
)


class TestRelativeLuminance:
    def test_black(self) -> None:
        assert relative_luminance(0, 0, 0) == pytest.approx(0.0, abs=1e-4)

    def test_white(self) -> None:
        assert relative_luminance(255, 255, 255) == pytest.approx(1.0, abs=1e-4)

    def test_mid_gray(self) -> None:
        lum = relative_luminance(128, 128, 128)
        assert 0.2 < lum < 0.3


class TestContrastRatio:
    def test_black_on_white(self) -> None:
        assert contrast_ratio("#000000", "#ffffff") == pytest.approx(21.0, abs=0.1)

    def test_same_color(self) -> None:
        assert contrast_ratio("#abcdef", "#abcdef") == pytest.approx(1.0, abs=0.1)

    def test_short_hex(self) -> None:
        assert contrast_ratio("#000", "#fff") == pytest.approx(21.0, abs=0.1)

    def test_returns_none_for_invalid_hex(self) -> None:
        assert contrast_ratio("red", "#fff") is None


class TestCheckContrast:
    def test_low_contrast_detected(self) -> None:
        line = AddedLine(
            number=5,
            content="  color: #777777; background-color: #888888;",
        )
        findings = check_contrast("style.css", [line])
        assert len(findings) == 1
        assert findings[0].axis == Axis.A11Y
        assert findings[0].line == 5
        assert findings[0].source == Source.RULE

    def test_good_contrast_no_finding(self) -> None:
        line = AddedLine(
            number=1,
            content="  color: #000000; background-color: #ffffff;",
        )
        assert check_contrast("style.css", [line]) == []

    def test_only_color_no_background_skipped(self) -> None:
        line = AddedLine(number=1, content="  color: #333;")
        assert check_contrast("style.css", [line]) == []

    def test_only_background_no_color_skipped(self) -> None:
        line = AddedLine(number=1, content="  background-color: #fff;")
        assert check_contrast("style.css", [line]) == []

    def test_non_css_file_skipped(self) -> None:
        line = AddedLine(
            number=1,
            content="color: #777; background-color: #888;",
        )
        assert check_contrast("main.py", [line]) == []

    def test_eligible_extensions(self) -> None:
        line = AddedLine(
            number=1,
            content="color: #777; background-color: #888;",
        )
        for ext in ("a.css", "b.scss", "c.less", "d.vue"):
            assert len(check_contrast(ext, [line])) == 1

    def test_background_shorthand(self) -> None:
        line = AddedLine(
            number=1,
            content="  color: #777; background: #888;",
        )
        findings = check_contrast("style.css", [line])
        assert len(findings) == 1
