from typing import Any

import pytest

from pairo.application.propose_context_rule import BRANCH, PATH, ProposeContextRule
from pairo.domain.context_rule import NO_RULE, RuleProposal

PR_URL = "https://github.com/o/r/pull/9"


class FakeHost:
    def __init__(self, files: dict[tuple[str, str], str] | None = None) -> None:
        self.files = files or {}
        self.proposals: list[dict[str, Any]] = []
        self.fail = False

    async def get_repo_file(
        self, owner: str, repo: str, path: str, ref: str
    ) -> str | None:
        return self.files.get((path, ref))

    async def propose_file_change(self, owner: str, repo: str, **kw: Any) -> str:
        if self.fail:
            raise RuntimeError("403")
        self.proposals.append(kw)
        return PR_URL


class FakeClassifier:
    def __init__(self, proposal: RuleProposal) -> None:
        self.proposal = proposal
        self.calls: list[tuple[str, str, str]] = []

    async def classify_rule(
        self, reason: str, finding_text: str, file: str
    ) -> RuleProposal:
        self.calls.append((reason, finding_text, file))
        return self.proposal


def _uc(host: FakeHost, proposal: RuleProposal) -> tuple[ProposeContextRule, Any]:
    classifier = FakeClassifier(proposal)
    return ProposeContextRule(host, classifier, threshold=0.7), classifier  # type: ignore[arg-type]


async def _run(uc: ProposeContextRule) -> str | None:
    return await uc.execute(
        owner="o",
        repo="r",
        default_branch="main",
        reason="we use Vue",
        finding_text="Prefer React",
        file="src/a.ts",
    )


async def test_durable_rule_above_threshold_opens_pr() -> None:
    host = FakeHost()
    uc, _ = _uc(host, RuleProposal(True, 0.9, "Use Vue"))
    reply = await _run(uc)
    assert reply is not None and PR_URL in reply
    assert len(host.proposals) == 1
    p = host.proposals[0]
    assert p["content"] == "# Pairo context\n- Use Vue\n"
    assert (p["branch"], p["path"], p["default_branch"]) == (BRANCH, PATH, "main")


async def test_below_threshold_does_nothing() -> None:
    host = FakeHost()
    uc, _ = _uc(host, RuleProposal(True, 0.69, "Use Vue"))
    assert await _run(uc) is None
    assert host.proposals == []


async def test_not_persisted_does_nothing() -> None:
    host = FakeHost()
    uc, _ = _uc(host, NO_RULE)
    assert await _run(uc) is None
    assert host.proposals == []


async def test_appends_to_existing_default_branch_file() -> None:
    host = FakeHost({(PATH, "main"): "# Pairo context\n- No jQuery\n"})
    uc, _ = _uc(host, RuleProposal(True, 0.9, "Use Vue"))
    await _run(uc)
    assert host.proposals[0]["content"] == "# Pairo context\n- No jQuery\n- Use Vue\n"


async def test_second_rule_does_not_overwrite_open_pr_content() -> None:
    host = FakeHost(
        {
            (PATH, BRANCH): "# Pairo context\n- First rule\n",
            (PATH, "main"): "# Pairo context\n",
        }
    )
    uc, _ = _uc(host, RuleProposal(True, 0.9, "Second rule"))
    await _run(uc)
    assert host.proposals[0]["content"] == (
        "# Pairo context\n- First rule\n- Second rule\n"
    )


async def test_duplicate_rule_replies_without_opening_pr() -> None:
    host = FakeHost({(PATH, "main"): "# Pairo context\n- Use Vue\n"})
    uc, _ = _uc(host, RuleProposal(True, 0.9, "use vue"))
    reply = await _run(uc)
    assert reply is not None and ".pairo.md" in reply
    assert host.proposals == []


async def test_code_host_failure_propagates() -> None:
    host = FakeHost()
    host.fail = True
    uc, _ = _uc(host, RuleProposal(True, 0.9, "Use Vue"))
    with pytest.raises(RuntimeError):
        await _run(uc)


async def test_classifier_receives_reason_finding_and_file() -> None:
    uc, classifier = _uc(FakeHost(), RuleProposal(True, 0.9, "Use Vue"))
    await _run(uc)
    assert classifier.calls == [("we use Vue", "Prefer React", "src/a.ts")]


async def test_disabled_in_pairo_yml_skips_everything() -> None:
    host = FakeHost({(".pairo.yml", "main"): "context:\n  propose_rules: false\n"})
    uc, classifier = _uc(host, RuleProposal(True, 0.9, "Use Vue"))
    assert await _run(uc) is None
    assert classifier.calls == []
    assert host.proposals == []
