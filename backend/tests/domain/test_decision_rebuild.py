"""Tests for rebuilding decisions from GitHub comment markers."""

import pytest

from pairo.domain.decision import DecisionStatus, FindingDecision
from pairo.domain.decision_rebuild import rebuild_decisions_from_comments
from pairo.domain.marker import build_marker


def _comment(
    body: str,
    *,
    comment_id: int = 1,
    reactions: list[str] | None = None,
    is_resolved: bool = False,
) -> dict:
    return {
        "id": comment_id,
        "body": body,
        "reactions": reactions or [],
        "is_resolved": is_resolved,
    }


class TestRebuildDecisions:
    def test_comment_with_marker_creates_posted_decision(self):
        marker = build_marker("fp1234567890abcd", "crafts", "naming")
        comments = [_comment(f"Some issue\n\n{marker}", comment_id=100)]

        decisions = rebuild_decisions_from_comments(
            comments, repo="acme/web", pr_number=5
        )
        assert len(decisions) == 1
        assert decisions[0].fingerprint == "fp1234567890abcd"
        assert decisions[0].status == DecisionStatus.POSTED
        assert decisions[0].github_comment_id == 100

    def test_comment_without_marker_ignored(self):
        comments = [_comment("Just a regular comment")]
        decisions = rebuild_decisions_from_comments(comments, "acme/web", 1)
        assert decisions == []

    def test_resolved_thread_marks_rejected(self):
        marker = build_marker("fp_resolved", "eco", "size")
        comments = [
            _comment(f"Too big\n\n{marker}", comment_id=200, is_resolved=True)
        ]
        decisions = rebuild_decisions_from_comments(comments, "acme/web", 1)
        assert len(decisions) == 1
        assert decisions[0].status == DecisionStatus.REJECTED

    def test_thumbs_down_reaction_marks_rejected(self):
        marker = build_marker("fp_thumbs", "a11y", "img-alt")
        comments = [
            _comment(
                f"Missing alt\n\n{marker}",
                comment_id=300,
                reactions=["-1"],
            )
        ]
        decisions = rebuild_decisions_from_comments(comments, "acme/web", 1)
        assert decisions[0].status == DecisionStatus.REJECTED

    def test_malformed_marker_ignored(self):
        comments = [_comment("<!-- pairo:garbage -->", comment_id=400)]
        decisions = rebuild_decisions_from_comments(comments, "acme/web", 1)
        assert decisions == []

    def test_multiple_comments_multiple_decisions(self):
        m1 = build_marker("fp_one", "crafts", "naming")
        m2 = build_marker("fp_two", "eco", "size")
        comments = [
            _comment(f"Issue 1\n\n{m1}", comment_id=1),
            _comment(f"Issue 2\n\n{m2}", comment_id=2),
        ]
        decisions = rebuild_decisions_from_comments(comments, "acme/web", 1)
        assert len(decisions) == 2
        fps = {d.fingerprint for d in decisions}
        assert fps == {"fp_one", "fp_two"}
