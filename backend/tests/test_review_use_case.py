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
        self.last_input_tokens: int = 0
        self.last_output_tokens: int = 0

    async def review(
        self,
        files: list[FileDiff],
        existing_findings: list[Finding],
        axes: list[str],
        language: str,
    ) -> list[Finding]:
        self.called = True
        self.last_input_tokens = 100
        self.last_output_tokens = 50
        return self._findings


class FakeReviewRepo:
    def __init__(self, today_count: int = 0) -> None:
        self.saved: list[Review] = []
        self._today_count = today_count

    async def save(self, review: Review) -> None:
        review.id = len(self.saved) + 1
        self.saved.append(review)

    async def exists(self, delivery_id: str) -> bool:
        return any(r.delivery_id == delivery_id for r in self.saved)

    async def get(self, review_id: int) -> Review | None:
        return next((r for r in self.saved if r.id == review_id), None)

    async def list_reviews(
        self, offset: int = 0, limit: int = 20,
    ) -> list[Review]:
        return self.saved[offset : offset + limit]

    async def today_review_count(self) -> int:
        return self._today_count


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


async def test_saves_review_to_repository() -> None:
    files = [FileDiff("main.py", [AddedLine(1, "x = 1")])]
    code_host = FakeCodeHost(files)
    llm = FakeLLM()
    repo = FakeReviewRepo()

    uc = ReviewPullRequest(
        code_host=code_host, llm_reviewer=llm, review_repo=repo,
    )
    await uc.execute(
        owner="acme", repo="web", pr_number=7, head_sha="abc",
        action="opened", delivery_id="d-1",
    )

    assert len(repo.saved) == 1
    saved = repo.saved[0]
    assert saved.delivery_id == "d-1"
    assert saved.owner == "acme"
    assert saved.repo == "web"
    assert saved.pr_number == 7
    assert saved.input_tokens == 100


async def test_degraded_mode_skips_llm_when_quota_exhausted() -> None:
    files = [
        FileDiff(
            "App.vue",
            [AddedLine(3, '  <img src="logo.png">')],
        ),
    ]
    code_host = FakeCodeHost(files)
    llm = FakeLLM()
    repo = FakeReviewRepo(today_count=50)

    uc = ReviewPullRequest(
        code_host=code_host, llm_reviewer=llm, review_repo=repo,
        daily_quota=50,
    )
    await uc.execute(
        owner="o", repo="r", pr_number=1, head_sha="abc", action="opened",
    )

    assert not llm.called
    assert code_host.posted_review is not None
    rule_findings = [
        f for f in code_host.posted_review.findings
        if f.source == Source.RULE
    ]
    assert len(rule_findings) >= 1


async def test_degraded_mode_not_triggered_when_under_quota() -> None:
    files = [FileDiff("main.py", [AddedLine(1, "x = 1")])]
    code_host = FakeCodeHost(files)
    llm = FakeLLM()
    repo = FakeReviewRepo(today_count=10)

    uc = ReviewPullRequest(
        code_host=code_host, llm_reviewer=llm, review_repo=repo,
        daily_quota=50,
    )
    await uc.execute(
        owner="o", repo="r", pr_number=1, head_sha="abc", action="opened",
    )

    assert llm.called


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
