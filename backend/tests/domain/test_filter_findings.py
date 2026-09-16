"""Tests for filtering findings against known decisions."""

from pairo.domain.decision import DecisionStatus, FindingDecision
from pairo.domain.filter_findings import filter_findings


def _decision(
    fingerprint: str, status: DecisionStatus
) -> FindingDecision:
    return FindingDecision(
        repo="acme/web",
        pr_number=1,
        fingerprint=fingerprint,
        axis="crafts",
        category="naming",
        status=status,
    )


class TestFilterFindings:
    def test_rejected_finding_removed(self):
        findings = {"fp1": {"issue": "bad name"}, "fp2": {"issue": "long fn"}}
        decisions = [_decision("fp1", DecisionStatus.REJECTED)]
        kept, filtered_count = filter_findings(findings, decisions)
        assert "fp1" not in kept
        assert "fp2" in kept
        assert filtered_count == 1

    def test_accepted_finding_removed(self):
        """Accepted = already dealt with, don't re-post."""
        findings = {"fp1": {"issue": "done"}}
        decisions = [_decision("fp1", DecisionStatus.ACCEPTED)]
        kept, filtered_count = filter_findings(findings, decisions)
        assert kept == {}
        assert filtered_count == 1

    def test_posted_finding_removed_as_duplicate(self):
        """Already posted on this PR = don't duplicate."""
        findings = {"fp1": {"issue": "already there"}}
        decisions = [_decision("fp1", DecisionStatus.POSTED)]
        kept, filtered_count = filter_findings(findings, decisions)
        assert kept == {}
        assert filtered_count == 1

    def test_resolved_with_change_not_filtered(self):
        """Code changed since rejection = finding is eligible again."""
        findings = {"fp1": {"issue": "new code"}}
        decisions = [_decision("fp1", DecisionStatus.RESOLVED_WITH_CHANGE)]
        kept, filtered_count = filter_findings(findings, decisions)
        assert "fp1" in kept
        assert filtered_count == 0

    def test_no_decisions_nothing_filtered(self):
        findings = {"fp1": {"issue": "a"}, "fp2": {"issue": "b"}}
        kept, filtered_count = filter_findings(findings, [])
        assert len(kept) == 2
        assert filtered_count == 0

    def test_empty_findings(self):
        kept, filtered_count = filter_findings(
            {}, [_decision("fp1", DecisionStatus.REJECTED)]
        )
        assert kept == {}
        assert filtered_count == 0

    def test_multiple_filtered(self):
        findings = {
            "fp1": {"issue": "a"},
            "fp2": {"issue": "b"},
            "fp3": {"issue": "c"},
        }
        decisions = [
            _decision("fp1", DecisionStatus.REJECTED),
            _decision("fp2", DecisionStatus.POSTED),
        ]
        kept, filtered_count = filter_findings(findings, decisions)
        assert list(kept.keys()) == ["fp3"]
        assert filtered_count == 2


class TestFilterSummaryLine:
    def test_summary_line(self):
        from pairo.domain.filter_findings import memory_summary_line

        assert memory_summary_line(0) == ""
        assert "1 remarque" in memory_summary_line(1)
        assert "3 remarques" in memory_summary_line(3)
