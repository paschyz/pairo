"""Deterministic cache key for LLM review results. Pure domain."""

import hashlib
import json


def compute_cache_key(
    *,
    files_content: dict[str, str],
    axes: list[str],
    config_hash: str,
    prompt_version: str,
    model: str,
) -> str:
    """SHA-256 of normalized inputs. Order-independent on files."""
    parts = {
        "files": dict(sorted(files_content.items())),
        "axes": sorted(axes),
        "config": config_hash,
        "prompt_version": prompt_version,
        "model": model,
    }
    payload = json.dumps(parts, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()
