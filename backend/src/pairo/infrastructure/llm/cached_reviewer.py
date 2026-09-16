"""LLM reviewer wrapper with deterministic cache."""

from typing import Any

from pairo.domain.cache_key import compute_cache_key
from pairo.domain.finding import Axis, Finding, Source
from pairo.domain.ports import FileDiff
from pairo.infrastructure.llm.prompt import PROMPT_VERSION
from pairo.infrastructure.persistence.finding_cache import SqlFindingCache


class CachedLLMReviewer:
    """Wraps an LLM reviewer with a deterministic cache layer."""

    def __init__(
        self,
        inner: Any,
        cache: SqlFindingCache,
        *,
        model: str,
        axes: list[str],
        config_hash: str = "",
        prompt_version: str = PROMPT_VERSION,
    ) -> None:
        self._inner = inner
        self._cache = cache
        self._model = model
        self._axes = axes
        self._config_hash = config_hash
        self._prompt_version = prompt_version

        # Proxy token attributes
        self.last_input_tokens: int = 0
        self.last_output_tokens: int = 0
        self.model_name: str = getattr(inner, "model_name", model)

        # Stats
        self.cache_hits: int = 0
        self.tokens_saved: int = 0

    async def review(
        self,
        files: list[FileDiff],
        existing_findings: list[Finding],
        axes: list[str],
        language: str,
    ) -> list[Finding]:
        # Build cache key from file contents
        files_content = {}
        for f in files:
            lines = "\n".join(
                f"{ln.number}: {ln.content}" for ln in f.added_lines
            )
            files_content[f.path] = lines

        key = compute_cache_key(
            files_content=files_content,
            axes=axes,
            config_hash=self._config_hash,
            prompt_version=self._prompt_version,
            model=self._model,
        )

        # Check cache
        cached = await self._cache.get(key)
        if cached is not None:
            self.cache_hits += 1
            self.tokens_saved += (
                cached["input_tokens"] + cached["output_tokens"]
            )
            self.last_input_tokens = 0
            self.last_output_tokens = 0
            return _parse_cached(cached["findings"])

        # Cache miss — delegate to inner LLM
        findings: list[Finding] = await self._inner.review(
            files, existing_findings, axes, language
        )
        self.last_input_tokens = self._inner.last_input_tokens
        self.last_output_tokens = self._inner.last_output_tokens

        # Store in cache
        raw = [
            {
                "axis": f.axis.value,
                "file": f.file,
                "line": f.line,
                "issue": f.issue,
                "suggestion": f.suggestion,
            }
            for f in findings
        ]
        await self._cache.put(
            key,
            raw,
            input_tokens=self.last_input_tokens,
            output_tokens=self.last_output_tokens,
        )

        return findings


def _parse_cached(raw: list[dict[str, Any]]) -> list[Finding]:
    findings: list[Finding] = []
    for item in raw:
        try:
            findings.append(
                Finding(
                    axis=Axis(item["axis"]),
                    file=item["file"],
                    line=item.get("line"),
                    issue=item["issue"],
                    suggestion=item["suggestion"],
                    source=Source.LLM,
                )
            )
        except (KeyError, ValueError):
            continue
    return findings
