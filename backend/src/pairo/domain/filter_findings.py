"""Filter findings against known decisions. Pure domain."""

from typing import Any

from pairo.domain.decision import DecisionStatus, FindingDecision

# Statuses that cause a finding to be suppressed
_SUPPRESS = {DecisionStatus.REJECTED, DecisionStatus.ACCEPTED, DecisionStatus.POSTED}


def filter_findings(
    findings_by_fp: dict[str, Any],
    decisions: list[FindingDecision],
) -> tuple[dict[str, Any], int]:
    """Remove findings whose fingerprint has a suppressing decision.

    Returns (kept_findings, filtered_count).
    """
    suppress_fps = {d.fingerprint for d in decisions if d.status in _SUPPRESS}

    kept: dict[str, Any] = {}
    filtered = 0
    for fp, finding in findings_by_fp.items():
        if fp in suppress_fps:
            filtered += 1
        else:
            kept[fp] = finding

    return kept, filtered


def memory_summary_line(filtered_count: int) -> str:
    """One-line summary for the review body."""
    if filtered_count == 0:
        return ""
    noun = "remarque" if filtered_count == 1 else "remarques"
    plural = filtered_count > 1
    s = "s" if plural else ""
    verb = "ont" if plural else "a"
    return (
        f"{filtered_count} {noun} déjà écartée{s}"
        f" sur cette PR n'{verb} pas été reposée{s}."
    )
