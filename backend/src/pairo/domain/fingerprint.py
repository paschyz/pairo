"""Content-based fingerprint for findings. Pure domain, no external deps."""

import hashlib
import re


def _normalize_lines(lines: list[str]) -> str:
    """Strip leading/trailing whitespace, collapse multiple spaces, drop blanks."""
    normalized = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        collapsed = re.sub(r"\s+", " ", stripped)
        normalized.append(collapsed)
    return "\n".join(normalized)


def compute_fingerprint(
    axis: str,
    category: str,
    file_path: str,
    context_lines: list[str],
    *,
    rule_id: str | None = None,
    blob_sha: str | None = None,
) -> str:
    """Return a 16-char hex fingerprint for a finding.

    For line-based findings: axis + category + path + normalized code context.
    For file-level findings (no lines): axis + category + path + rule_id + blob_sha.
    Deterministic rules may add rule_id for extra specificity.
    """
    parts = [axis, category, file_path]

    normalized = _normalize_lines(context_lines)
    if normalized:
        parts.append(normalized)

    if rule_id:
        parts.append(rule_id)

    if blob_sha:
        parts.append(blob_sha)

    payload = "\0".join(parts)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]
