"""Turn a durable `@pairo ignore <reason>` into a PR adding a rule to .pairo.md."""

from pairo.domain.context_rule import accept, merge_rule
from pairo.domain.ports import CodeHost, RuleClassifier
from pairo.domain.repo_config import parse_repo_config

BRANCH = "pairo/context"
PATH = ".pairo.md"


class ProposeContextRule:
    def __init__(
        self, code_host: CodeHost, classifier: RuleClassifier, threshold: float
    ) -> None:
        self._host = code_host
        self._classifier = classifier
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
        """Reply text for the thread, or None to stay silent."""
        raw_config = await self._host.get_repo_file(
            owner, repo, ".pairo.yml", default_branch
        )
        if not parse_repo_config(raw_config).context_propose_rules:
            return None

        proposal = await self._classifier.classify_rule(reason, finding_text, file)
        if not accept(proposal, self._threshold):
            return None

        # An open Pairo PR already holds earlier rules: build on it, don't overwrite.
        existing = await self._host.get_repo_file(owner, repo, PATH, BRANCH)
        if existing is None:
            existing = await self._host.get_repo_file(owner, repo, PATH, default_branch)
        merged = merge_rule(existing, proposal.rule)
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
                f"> {proposal.rule}\n\n"
                "Merge to apply it, or edit `.pairo.md` freely before merging."
            ),
        )
        return f"Rule proposed in `.pairo.md`: {url}"
