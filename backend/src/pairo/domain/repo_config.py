import fnmatch
import logging
from dataclasses import dataclass, field

import yaml

logger = logging.getLogger(__name__)

_DEFAULT_AXES = ["crafts", "eco", "a11y"]
_DEFAULT_MAX_IMAGE_KB = 200
_DEFAULT_LANGUAGE = "fr"


@dataclass
class RepoConfig:
    axes: list[str] = field(default_factory=lambda: list(_DEFAULT_AXES))
    max_image_kb: int = 200
    ignore: list[str] = field(default_factory=list)
    ignore_categories: list[str] = field(default_factory=list)
    language: str = "fr"
    parse_error: str | None = None

    def should_ignore(self, path: str) -> bool:
        return any(fnmatch.fnmatch(path, pattern) for pattern in self.ignore)

    def should_ignore_category(self, axis: str, category: str) -> bool:
        qualified = f"{axis}.{category}"
        return any(
            fnmatch.fnmatch(qualified, pattern)
            for pattern in self.ignore_categories
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
    return RepoConfig(
        axes=data.get("axes", _DEFAULT_AXES),
        max_image_kb=data.get("max_image_kb", _DEFAULT_MAX_IMAGE_KB),
        ignore=data.get("ignore", []),
        ignore_categories=data.get("ignore_categories", []),
        language=data.get("language", _DEFAULT_LANGUAGE),
    )
