from pairo.application.review_pull_request import ReviewPullRequest
from pairo.domain.context_rule import MAX_FILE_CHARS
from pairo.domain.diff import AddedLine
from pairo.domain.finding import Axis, Finding, Source
from pairo.domain.ports import FileDiff
from pairo.domain.review import Review


class FakeCodeHost:
    def __init__(
        self,
        files: list[FileDiff],
        config_yaml: str | None = None,
        pairo_md: str | None = None,
    ) -> None:
        self._files = files
        self._repo_files = {".pairo.yml": config_yaml, ".pairo.md": pairo_md}
        self.fetched: list[tuple[str, str]] = []
        self.posted_review: Review | None = None

    async def get_pull_request_files(
        self, owner: str, repo: str, pr_number: int
    ) -> list[FileDiff]:
        return self._files

    async def get_compare_files(
        self, owner: str, repo: str, base: str, head: str
    ) -> list[FileDiff]:
        return self._files

    async def get_file_size_kb(self, owner: str, repo: str, path: str, ref: str) -> int:
        return 50

    async def post_review(
        self, owner: str, repo: str, pr_number: int, review: Review
    ) -> None:
        self.posted_review = review

    async def get_repo_file(
        self, owner: str, repo: str, path: str, ref: str
    ) -> str | None:
        self.fetched.append((path, ref))
        return self._repo_files.get(path)


class FakeLLM:
    def __init__(self, findings: list[Finding] | None = None) -> None:
        self._findings = findings or []
        self.called = False
        self.project_context: str | None = None
        self.last_input_tokens: int = 0
        self.last_output_tokens: int = 0

    async def review(
        self,
        files: list[FileDiff],
        existing_findings: list[Finding],
        axes: list[str],
        language: str,
        project_context: str = "",
    ) -> list[Finding]:
        self.called = True
        self.project_context = project_context
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
        self,
        offset: int = 0,
        limit: int = 20,
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
        code_host=code_host,
        llm_reviewer=llm,
        review_repo=repo,
    )
    await uc.execute(
        owner="acme",
        repo="web",
        pr_number=7,
        head_sha="abc",
        action="opened",
        delivery_id="d-1",
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
        code_host=code_host,
        llm_reviewer=llm,
        review_repo=repo,
        daily_quota=50,
    )
    await uc.execute(
        owner="o",
        repo="r",
        pr_number=1,
        head_sha="abc",
        action="opened",
    )

    assert not llm.called
    assert code_host.posted_review is not None
    rule_findings = [
        f for f in code_host.posted_review.findings if f.source == Source.RULE
    ]
    assert len(rule_findings) >= 1


async def test_degraded_mode_not_triggered_when_under_quota() -> None:
    files = [FileDiff("main.py", [AddedLine(1, "x = 1")])]
    code_host = FakeCodeHost(files)
    llm = FakeLLM()
    repo = FakeReviewRepo(today_count=10)

    uc = ReviewPullRequest(
        code_host=code_host,
        llm_reviewer=llm,
        review_repo=repo,
        daily_quota=50,
    )
    await uc.execute(
        owner="o",
        repo="r",
        pr_number=1,
        head_sha="abc",
        action="opened",
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


async def test_invalid_code_suggestion_stripped_but_finding_kept() -> None:
    from pairo.domain.finding import CodeSuggestion

    files = [FileDiff("main.py", [AddedLine(1, "x = 1")])]
    bad = Finding(
        axis=Axis.CRAFTS,
        file="main.py",
        line=99,
        issue="t",
        suggestion="fix",
        source=Source.LLM,
        code_suggestion=CodeSuggestion("y = 2"),
    )
    good = Finding(
        axis=Axis.CRAFTS,
        file="main.py",
        line=1,
        issue="u",
        suggestion="fix",
        source=Source.LLM,
        code_suggestion=CodeSuggestion("y = 2"),
    )
    code_host = FakeCodeHost(files)
    uc = ReviewPullRequest(code_host=code_host, llm_reviewer=FakeLLM([bad, good]))
    await uc.execute(owner="o", repo="r", pr_number=1, head_sha="abc", action="opened")

    assert code_host.posted_review is not None
    by_line = {f.line: f for f in code_host.posted_review.findings}
    assert by_line[99].code_suggestion is None
    assert by_line[1].code_suggestion == CodeSuggestion("y = 2")


async def test_resolved_thread_suppresses_finding_without_command() -> None:
    from pairo.domain.fingerprint import fingerprint_for
    from pairo.domain.marker import build_marker

    finding = Finding(
        axis=Axis.CRAFTS,
        file="a.py",
        line=1,
        issue="Bad",
        suggestion="Fix",
        source=Source.LLM,
    )
    host = FakeCodeHost([FileDiff(path="a.py", added_lines=[AddedLine(1, "x")])])
    marker = build_marker(fingerprint_for(finding), "crafts", "")

    async def threads(*_: object) -> list[dict[str, object]]:
        return [{"is_resolved": True, "comment_id": 5, "body": f"Bad {marker}"}]

    async def reactions(*_: object) -> list[str]:
        return []

    host.get_review_threads = threads  # type: ignore[attr-defined]
    host.get_comment_reactions = reactions  # type: ignore[attr-defined]

    class Repo:
        saved: list[object] = []

        async def get_decisions(self, *_: object) -> list[object]:
            return self.saved

        async def save(self, d: object) -> None:
            self.saved.append(d)

    uc = ReviewPullRequest(host, FakeLLM([finding]), decision_repo=Repo())
    await uc.execute(owner="o", repo="r", pr_number=1, head_sha="s", action="opened")
    assert host.posted_review is not None
    assert host.posted_review.findings == []


async def _review_with(code_host: FakeCodeHost, llm: FakeLLM, **kw: object) -> None:
    uc = ReviewPullRequest(code_host=code_host, llm_reviewer=llm, **kw)  # type: ignore[arg-type]
    await uc.execute(
        owner="o",
        repo="r",
        pr_number=1,
        head_sha="abc",
        action="opened",
        base_ref="main",
    )


def _one_file() -> list[FileDiff]:
    return [FileDiff("main.py", [AddedLine(1, "x = 1")])]


async def test_pairo_md_from_base_branch_reaches_the_llm() -> None:
    code_host = FakeCodeHost(_one_file(), pairo_md="# Pairo context\n- No Redis\n")
    llm = FakeLLM()
    await _review_with(code_host, llm)
    assert llm.project_context == "# Pairo context\n- No Redis\n"
    assert (".pairo.md", "main") in code_host.fetched


async def test_missing_pairo_md_gives_empty_context() -> None:
    llm = FakeLLM()
    await _review_with(FakeCodeHost(_one_file()), llm)
    assert llm.project_context == ""


async def test_oversized_pairo_md_is_capped() -> None:
    llm = FakeLLM()
    await _review_with(FakeCodeHost(_one_file(), pairo_md="x" * 20000), llm)
    assert llm.project_context == "x" * MAX_FILE_CHARS


async def test_pairo_md_not_fetched_when_llm_is_skipped() -> None:
    code_host = FakeCodeHost(_one_file(), pairo_md="- No Redis")
    llm = FakeLLM()
    await _review_with(
        code_host, llm, review_repo=FakeReviewRepo(today_count=50), daily_quota=50
    )
    assert not llm.called
    assert all(path != ".pairo.md" for path, _ in code_host.fetched)
