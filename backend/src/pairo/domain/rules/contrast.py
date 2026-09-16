import re

from pairo.domain.diff import AddedLine
from pairo.domain.finding import Axis, Finding, Source

_ELIGIBLE_EXTENSIONS = (".css", ".scss", ".less", ".vue")
_WCAG_AA_THRESHOLD = 4.5

_HEX_COLOR = re.compile(r"#([0-9a-fA-F]{3,8})\b")
_COLOR_PROP = re.compile(r"(?<![-\w])color\s*:\s*")
_BG_PROP = re.compile(r"background(?:-color)?\s*:\s*")


def _parse_hex(hex_str: str) -> tuple[int, int, int] | None:
    h = hex_str.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    if len(h) not in (6, 8):
        return None
    try:
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return None


def _srgb_to_linear(c: int) -> float:
    s = c / 255.0
    return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4


def relative_luminance(r: int, g: int, b: int) -> float:
    lr, lg, lb = _srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b)
    return 0.2126 * lr + 0.7152 * lg + 0.0722 * lb


def contrast_ratio(hex1: str, hex2: str) -> float | None:
    c1 = _parse_hex(hex1)
    c2 = _parse_hex(hex2)
    if c1 is None or c2 is None:
        return None
    l1 = relative_luminance(*c1)
    l2 = relative_luminance(*c2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _find_hex_after(pattern: re.Pattern[str], text: str) -> str | None:
    m = pattern.search(text)
    if not m:
        return None
    rest = text[m.end() :]
    hm = _HEX_COLOR.search(rest)
    return hm.group(0) if hm else None


def check_contrast(path: str, added_lines: list[AddedLine]) -> list[Finding]:
    if not path.endswith(_ELIGIBLE_EXTENSIONS):
        return []

    findings: list[Finding] = []
    for line in added_lines:
        fg = _find_hex_after(_COLOR_PROP, line.content)
        bg = _find_hex_after(_BG_PROP, line.content)
        if fg is None or bg is None:
            continue
        ratio = contrast_ratio(fg, bg)
        if ratio is not None and ratio < _WCAG_AA_THRESHOLD:
            findings.append(
                Finding(
                    axis=Axis.A11Y,
                    file=path,
                    line=line.number,
                    issue=(
                        f"Ratio de contraste insuffisant"
                        f" ({ratio:.1f}:1 < {_WCAG_AA_THRESHOLD}:1)"
                    ),
                    suggestion=(
                        "Ajuster les couleurs pour atteindre"
                        " un ratio d'au moins 4.5:1 (AA)"
                    ),
                    source=Source.RULE,
                )
            )
    return findings
