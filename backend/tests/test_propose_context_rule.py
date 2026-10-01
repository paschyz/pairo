from typing import Any

import pytest

from pairo.application.propose_context_rule import BRANCH, PATH, ProposeContextRule
from pairo.domain.context_rule import NO_VERDICT, RuleVerdict

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


class FakeLLM:
    """Plays the judge (verdict) or the writer (rule), recording its calls."""

    def __init__(self, verdict: RuleVerdict = NO_VERDICT, rule: str = "") -> None:
        self.verdict = verdict
        self.rule = rule
        self.calls: list[tuple[str, str, str]] = []

    async def judge_rule(
        self, reason: str, finding_text: str, file: str
    ) -> RuleVerdict:
        self.calls.append((reason, finding_text, file))
        return self.verdict

    async def write_rule(self, reason: str, finding_text: str, file: str) -> str:
        self.calls.append((reason, finding_text, file))
        return self.rule


def _uc(
    host: FakeHost, verdict: RuleVerdict, rule: str = "Use Vue"
) -> tuple[ProposeContextRule, FakeLLM, FakeLLM]:
    judge, writer = FakeLLM(verdict=verdict), FakeLLM(rule=rule)
    uc = ProposeContextRule(host, judge, writer, threshold=0.7)  # type: ignore[arg-type]
    return uc, judge, writer


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
    uc, _, _ = _uc(host, RuleVerdict(True, 0.9))
    reply = await _run(uc)
    assert reply is not None and PR_URL in reply
    assert len(host.proposals) == 1
    p = host.proposals[0]
    assert p["content"] == "# Pairo context\n- Use Vue\n"
    assert (p["branch"], p["path"], p["default_branch"]) == (BRANCH, PATH, "main")


async def test_below_threshold_does_nothing() -> None:
    host = FakeHost()
    uc, _, writer = _uc(host, RuleVerdict(True, 0.69))
    assert await _run(uc) is None
    assert host.proposals == []
    assert writer.calls == []


async def test_not_persisted_does_nothing() -> None:
    host = FakeHost()
    uc, _, writer = _uc(host, NO_VERDICT)
    assert await _run(uc) is None
    assert host.proposals == []
    assert writer.calls == []


async def test_blank_written_rule_does_nothing() -> None:
    host = FakeHost()
    uc, _, _ = _uc(host, RuleVerdict(True, 0.9), rule="")
    assert await _run(uc) is None
    assert host.proposals == []


async def test_appends_to_existing_default_branch_file() -> None:
    host = FakeHost({(PATH, "main"): "# Pairo context\n- No jQuery\n"})
    uc, _, _ = _uc(host, RuleVerdict(True, 0.9))
    await _run(uc)
    assert host.proposals[0]["content"] == "# Pairo context\n- No jQuery\n- Use Vue\n"


async def test_second_rule_does_not_overwrite_open_pr_content() -> None:
    host = FakeHost(
        {
            (PATH, BRANCH): "# Pairo context\n- First rule\n",
            (PATH, "main"): "# Pairo context\n",
        }
    )
    uc, _, _ = _uc(host, RuleVerdict(True, 0.9), rule="Second rule")
    await _run(uc)
    assert host.proposals[0]["content"] == (
        "# Pairo context\n- First rule\n- Second rule\n"
    )


async def test_duplicate_rule_replies_without_opening_pr() -> None:
    host = FakeHost({(PATH, "main"): "# Pairo context\n- Use Vue\n"})
    uc, _, _ = _uc(host, RuleVerdict(True, 0.9), rule="use vue")
    reply = await _run(uc)
    assert reply is not None and ".pairo.md" in reply
    assert host.proposals == []


async def test_code_host_failure_propagates() -> None:
    host = FakeHost()
    host.fail = True
    uc, _, _ = _uc(host, RuleVerdict(True, 0.9))
    with pytest.raises(RuntimeError):
        await _run(uc)


async def test_judge_and_writer_receive_reason_finding_and_file() -> None:
    uc, judge, writer = _uc(FakeHost(), RuleVerdict(True, 0.9))
    await _run(uc)
    assert judge.calls == [("we use Vue", "Prefer React", "src/a.ts")]
    assert writer.calls == judge.calls


async def test_disabled_in_pairo_yml_skips_everything() -> None:
    host = FakeHost({(".pairo.yml", "main"): "context:\n  propose_rules: false\n"})
    uc, judge, writer = _uc(host, RuleVerdict(True, 0.9))
    assert await _run(uc) is None
    assert judge.calls == writer.calls == []
    assert host.proposals == []
