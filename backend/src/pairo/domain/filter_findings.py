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
    noun = "comment" if filtered_count == 1 else "comments"
    return (
        f"{filtered_count} previously dismissed {noun}"
        f" on this PR {'was' if filtered_count == 1 else 'were'} not reposted."
    )


_SUGGEST_THRESHOLD = 3


def suggest_persistent_rule(qualified_category: str, rejected_pr_count: int) -> str:
    """Suggest adding to .pairo.yml if a category is rejected often."""
    if rejected_pr_count < _SUGGEST_THRESHOLD:
        return ""
    return (
        f"This comment (`{qualified_category}`) was dismissed"
        f" on {rejected_pr_count} PRs. To stop receiving it,"
        f" add to `.pairo.yml`:\n"
        f"```yaml\n"
        f'ignore_categories: ["{qualified_category}"]\n'
        f"```"
    )
