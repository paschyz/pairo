"""Hidden HTML marker in Pairo review comments. Pure domain."""

import re

_MARKER_RE = re.compile(r"<!--\s*pairo:(.*?)\s*-->")
_REQUIRED_KEYS = {"fp", "axis", "cat", "v"}


def build_marker(fingerprint: str, axis: str, category: str) -> str:
    return f"<!-- pairo:fp={fingerprint};axis={axis};cat={category};v=1 -->"


def parse_marker(text: str) -> dict[str, str] | None:
    """Extract marker fields from comment text. Returns None if absent/malformed."""
    match = _MARKER_RE.search(text)
    if not match:
        return None

    raw = match.group(1)
    pairs: dict[str, str] = {}
    for part in raw.split(";"):
        if "=" not in part:
            return None
        key, value = part.split("=", 1)
        pairs[key.strip()] = value.strip()

    if not _REQUIRED_KEYS.issubset(pairs):
        return None

    return pairs
