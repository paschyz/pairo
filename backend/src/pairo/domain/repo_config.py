import fnmatch
import logging
from dataclasses import dataclass, field

import yaml

logger = logging.getLogger(__name__)

_DEFAULTS = {
    "axes": ["crafts", "eco", "a11y"],
    "max_image_kb": 200,
    "ignore": [],
    "language": "fr",
}


@dataclass
class RepoConfig:
    axes: list[str] = field(default_factory=lambda: list(_DEFAULTS["axes"]))  # type: ignore[arg-type]
    max_image_kb: int = 200
    ignore: list[str] = field(default_factory=list)
    language: str = "fr"
    parse_error: str | None = None

    def should_ignore(self, path: str) -> bool:
        return any(fnmatch.fnmatch(path, pattern) for pattern in self.ignore)


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
        axes=data.get("axes", _DEFAULTS["axes"]),
        max_image_kb=data.get("max_image_kb", _DEFAULTS["max_image_kb"]),
        ignore=data.get("ignore", _DEFAULTS["ignore"]),
        language=data.get("language", _DEFAULTS["language"]),
    )
