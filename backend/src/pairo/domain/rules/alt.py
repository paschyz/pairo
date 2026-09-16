import re

from pairo.domain.diff import AddedLine
from pairo.domain.finding import Axis, Finding, Source

_ELIGIBLE_EXTENSIONS = (".html", ".jsx", ".tsx", ".vue")
_IMG_TAG = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_HAS_ALT = re.compile(r"""\balt\s*=\s*["']""", re.IGNORECASE)


def check_missing_alt(path: str, added_lines: list[AddedLine]) -> list[Finding]:
    if not path.endswith(_ELIGIBLE_EXTENSIONS):
        return []

    findings: list[Finding] = []
    for line in added_lines:
        if _IMG_TAG.search(line.content) and not _HAS_ALT.search(line.content):
            findings.append(
                Finding(
                    axis=Axis.A11Y,
                    file=path,
                    line=line.number,
                    issue="<img> sans attribut `alt`",
                    suggestion="Ajouter `alt=\"description\"` ou `alt=\"\"` si décorative",
                    source=Source.RULE,
                )
            )
    return findings
