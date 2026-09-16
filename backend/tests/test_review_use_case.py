from pairo.application.review_pull_request import ReviewPullRequest
from pairo.domain.diff import AddedLine
from pairo.domain.finding import Axis, Finding, Source
from pairo.domain.ports import FileDiff
from pairo.domain.review import Review


class FakeCodeHost:
    def __init__(self, files: list[FileDiff], config_yaml: str | None = None) -> None:
        self._files = files
        self._config_yaml = config_yaml
        self.posted_review: Review | None = None

    async def get_pull_request_files(
        self, owner: str, repo: str, pr_number: int
    ) -> list[FileDiff]:
        return self._files

    async def get_compare_files(
        self, owner: str, repo: str, base: str, head: str
    ) -> list[FileDiff]:
        return self._files

    async def get_file_size_kb(
        self, owner: str, repo: str, path: str, ref: str
    ) -> int:
        return 50

    async def post_review(
        self, owner: str, repo: str, pr_number: int, review: Review
    ) -> None:
        self.posted_review = review

    async def get_repo_file(
        self, owner: str, repo: str, path: str, ref: str
    ) -> str | None:
        return self._config_yaml


class FakeLLM:
    def __init__(self, findings: list[Finding] | None = None) -> None:
        self._findings = findings or []
        self.called = False

    async def review(
        self,
        files: list[FileDiff],
        existing_findings: list[Finding],
        axes: list[str],
        language: str,
    ) -> list[Finding]:
        self.called = True
        return self._findings


async def test_runs_rules_and_posts_review() -> None:
    files = [
        FileDiff(
            "App.vue",
            [AddedLine(3, '  <img src="logo.png">')],
        ),
    ]
    code_host = FakeCodeHost(files)
    llm = FakeLLM()

    uc = ReviewPullRequest(code_host=code_host, llm_reviewer=llm)
    await uc.execute(
        owner="o",
        repo="r",
        pr_number=1,
        head_sha="abc",
        action="opened",
    )

    assert code_host.posted_review is not None
    review = code_host.posted_review
    rule_findings = [f for f in review.findings if f.source == Source.RULE]
    assert len(rule_findings) >= 1
    assert any(f.axis == Axis.A11Y for f in rule_findings)


async def test_calls_llm_reviewer() -> None:
    files = [FileDiff("main.py", [AddedLine(1, "x = 1")])]
    llm_finding = Finding(
        axis=Axis.CRAFTS,
        file="main.py",
        line=1,
        issue="test",
        suggestion="fix",
        source=Source.LLM,
    )
    code_host = FakeCodeHost(files)
    llm = FakeLLM([llm_finding])

    uc = ReviewPullRequest(code_host=code_host, llm_reviewer=llm)
    await uc.execute(owner="o", repo="r", pr_number=1, head_sha="abc", action="opened")

    assert llm.called
    assert code_host.posted_review is not None
    assert llm_finding in code_host.posted_review.findings


async def test_posts_review_even_with_no_findings() -> None:
    files = [FileDiff("main.py", [AddedLine(1, "x = 1")])]
    code_host = FakeCodeHost(files)
    llm = FakeLLM()

    uc = ReviewPullRequest(code_host=code_host, llm_reviewer=llm)
    await uc.execute(owner="o", repo="r", pr_number=1, head_sha="abc", action="opened")

    assert code_host.posted_review is not None
    assert code_host.posted_review.total == 0


async def test_no_review_when_no_added_lines() -> None:
    files: list[FileDiff] = []
    code_host = FakeCodeHost(files)
    llm = FakeLLM()

    uc = ReviewPullRequest(code_host=code_host, llm_reviewer=llm)
    await uc.execute(owner="o", repo="r", pr_number=1, head_sha="abc", action="opened")

    assert code_host.posted_review is not None
    assert not llm.called


async def test_reads_repo_config() -> None:
    files = [
        FileDiff(
            "App.vue",
            [AddedLine(3, '  <img src="logo.png">')],
        ),
    ]
    code_host = FakeCodeHost(files, config_yaml="axes: [eco]")
    llm = FakeLLM()

    uc = ReviewPullRequest(code_host=code_host, llm_reviewer=llm)
    await uc.execute(owner="o", repo="r", pr_number=1, head_sha="abc", action="opened")

    assert code_host.posted_review is not None
    # a11y rule should not fire because a11y is not in axes
    a11y = [f for f in code_host.posted_review.findings if f.axis == Axis.A11Y]
    assert a11y == []


async def test_uses_compare_for_synchronize() -> None:
    files = [FileDiff("new.ts", [AddedLine(1, "export const x = 1;")])]
    code_host = FakeCodeHost(files)
    llm = FakeLLM()

    uc = ReviewPullRequest(code_host=code_host, llm_reviewer=llm)
    await uc.execute(
        owner="o",
        repo="r",
        pr_number=1,
        head_sha="def",
        action="synchronize",
        before_sha="abc",
    )

    assert code_host.posted_review is not None
