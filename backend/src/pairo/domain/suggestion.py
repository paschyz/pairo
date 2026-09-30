from dataclasses import replace

from pairo.domain.finding import Finding
from pairo.domain.ports import FileDiff

MAX_RANGE_LINES = 20
MAX_REPLACEMENT_LINES = 50


def _is_valid(finding: Finding, added: dict[str, set[int]]) -> bool:
    cs = finding.code_suggestion
    if cs is None or not cs.replacement.strip() or finding.line is None:
        return False
    if len(cs.replacement.splitlines()) > MAX_REPLACEMENT_LINES:
        return False
    end = cs.end_line if cs.end_line is not None else finding.line
    if end < finding.line or end - finding.line + 1 > MAX_RANGE_LINES:
        return False
    # Every replaced line must be an added (hence commentable) line of the diff.
    return set(range(finding.line, end + 1)) <= added.get(finding.file, set())


def sanitize_suggestions(
    findings: list[Finding], files: list[FileDiff]
) -> tuple[list[Finding], int]:
    """Drop code suggestions that don't map onto added diff lines.

    The finding itself is always kept (as a plain comment). Returns the
    findings and the number of suggestions dropped.
    """
    added = {f.path: {a.number for a in f.added_lines} for f in files}
    out: list[Finding] = []
    dropped = 0
    for finding in findings:
        if finding.code_suggestion is not None and not _is_valid(finding, added):
            dropped += 1
            finding = replace(finding, code_suggestion=None)
        out.append(finding)
    return out, dropped
