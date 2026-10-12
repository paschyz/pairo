import fnmatch
import logging
import re
from dataclasses import dataclass, field

import yaml

logger = logging.getLogger(__name__)

_DEFAULT_AXES = ["crafts", "eco", "a11y"]
_DEFAULT_MAX_IMAGE_KB = 200
_DEFAULT_LANGUAGE = "en"
_LANGUAGE_RE = re.compile(r"[A-Za-z]{2,3}(-[A-Za-z]{2,4})?")


@dataclass
class RepoConfig:
    axes: list[str] = field(default_factory=lambda: list(_DEFAULT_AXES))
    max_image_kb: int = 200
    ignore: list[str] = field(default_factory=list)
    ignore_categories: list[str] = field(default_factory=list)
    language: str = "en"
    memory_enabled: bool = True
    memory_classify_replies: bool = False
    context_propose_rules: bool = True
    parse_error: str | None = None

    def should_ignore(self, path: str) -> bool:
        return any(fnmatch.fnmatch(path, pattern) for pattern in self.ignore)

    def should_ignore_category(self, axis: str, category: str) -> bool:
        qualified = f"{axis}.{category}"
        return any(
            fnmatch.fnmatch(qualified, pattern) for pattern in self.ignore_categories
        )


def parse_repo_config(raw: str | None) -> RepoConfig:
    if not raw:
        return RepoConfig()
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        return RepoConfig(parse_error=str(e))
    if not isinstance(data, dict):
        return RepoConfig()
    memory = data.get("memory", {})
    if not isinstance(memory, dict):
        memory = {}
    context = data.get("context", {})
    if not isinstance(context, dict):
        context = {}
    # The file is written by repo users: a wrong type must not crash the review,
    # and free text must not reach the LLM prompt (axes and language are sent to it).
    axes = data.get("axes")
    max_kb = data.get("max_image_kb")
    language = data.get("language")
    return RepoConfig(
        axes=[a for a in _strings(axes) if a in _DEFAULT_AXES]
        if isinstance(axes, list)
        else list(_DEFAULT_AXES),
        max_image_kb=max_kb
        if isinstance(max_kb, int) and not isinstance(max_kb, bool) and max_kb > 0
        else _DEFAULT_MAX_IMAGE_KB,
        ignore=_strings(data.get("ignore")),
        ignore_categories=_strings(data.get("ignore_categories")),
        language=language
        if isinstance(language, str) and _LANGUAGE_RE.fullmatch(language)
        else _DEFAULT_LANGUAGE,
        memory_enabled=_flag(memory.get("enabled"), True),
        memory_classify_replies=_flag(memory.get("classify_replies"), False),
        context_propose_rules=_flag(context.get("propose_rules"), True),
    )


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [v for v in value if isinstance(v, str)]


def _flag(value: object, default: bool) -> bool:
    return value if isinstance(value, bool) else default
