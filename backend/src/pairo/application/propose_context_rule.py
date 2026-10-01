"""Turn a durable `@pairo ignore <reason>` into a PR adding a rule to .pairo.md."""

from pairo.domain.context_rule import accept, merge_rule
from pairo.domain.ports import CodeHost, RuleJudge, RuleWriter
from pairo.domain.repo_config import parse_repo_config

BRANCH = "pairo/context"
PATH = ".pairo.md"


class ProposeContextRule:
    def __init__(
        self,
        code_host: CodeHost,
        judge: RuleJudge,
        writer: RuleWriter,
        threshold: float,
    ) -> None:
        self._host = code_host
        self._judge = judge
        self._writer = writer
        self._threshold = threshold

    async def execute(
        self,
        *,
        owner: str,
        repo: str,
        default_branch: str,
        reason: str,
        finding_text: str,
        file: str,
    ) -> str | None:
        """Outcome line for the thread reply, or None when no rule is proposed."""
        raw_config = await self._host.get_repo_file(
            owner, repo, ".pairo.yml", default_branch
        )
        if not parse_repo_config(raw_config).context_propose_rules:
            return None

        verdict = await self._judge.judge_rule(reason, finding_text, file)
        if not accept(verdict, self._threshold):
            return None
        rule = await self._writer.write_rule(reason, finding_text, file)
        if not rule.strip():
            return None

        # An open Pairo PR already holds earlier rules: build on it, don't overwrite.
        existing = await self._host.get_repo_file(owner, repo, PATH, BRANCH)
        if existing is None:
            existing = await self._host.get_repo_file(owner, repo, PATH, default_branch)
        merged = merge_rule(existing, rule)
        if merged is None:
            return (
                "Not added to `.pairo.md`: the rule is already there "
                "or the file is full."
            )

        url = await self._host.propose_file_change(
            owner,
            repo,
            default_branch=default_branch,
            branch=BRANCH,
            path=PATH,
            content=merged,
            message="docs: update .pairo.md",
            title="Add Pairo context rule",
            body=(
                "Pairo proposes this rule after a review reply.\n\n"
                f"> {rule}\n\n"
                "Merge to apply it, or edit `.pairo.md` freely before merging."
            ),
        )
        return f"Rule proposed in `.pairo.md`: {url}"
