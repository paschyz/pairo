# ADR 001 — Pairo memory architecture

**Status:** Accepted
**Date:** 2026-09-16

## Context

Users of AI reviewers complain about three problems:
- The bot re-suggests what was explicitly rejected
- Every push generates comments on unchanged code
- Re-running without changes gives different results

## Decisions

### 1. Content-based fingerprint, not line numbers

Line numbers change on every push. The fingerprint uses normalized code (whitespace-insensitive, blank-line-tolerant) + axis + category + path. Moving code without modifying it keeps the same fingerprint.

**Rejected alternative:** fingerprint by line number — too fragile, invalidated on every rebase.

### 2. Deterministic signals take priority over LLM interpretation

Priority order:
1. Explicit commands (`@pairo ignore/valid`)
2. Reactions (thumbs-down)
3. Thread resolved without a code change
4. LLM classification of free-form replies (optional, disabled by default)

The first three signals are free, deterministic, and consume no quota. The LLM only steps in for ambiguous cases, and only if enabled.

**Rejected alternative:** classify everything with the LLM — costly, non-deterministic, unpredictable results.

### 3. Visible memory: markers + versioned config

Every comment contains an invisible HTML marker with the fingerprint. If the database is lost, decisions are rebuilt from GitHub. Persistent rules go through `.pairo.yml` (versioned, visible, a human decides).

**Rejected alternative:** automatic learning of repo-wide rules — opaque, irreversible, no human control.

### 4. Deterministic cache via prompt versioning

The cache key includes `PROMPT_VERSION`, the model name, and the config. Any change naturally invalidates the cache. Configurable TTL as an extra safety net.

**Rejected alternative:** cache by full-prompt hash — fragile to minor rewordings that do not change the semantics.

## Consequences

- Rejections are immediate and free (no LLM call)
- The cache reduces LLM calls on re-reviews
- Memory is transparent and controllable
- No magic: the human keeps control through commands and `.pairo.yml`
