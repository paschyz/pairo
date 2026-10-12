# Hardening pass: what a reviewer could break, and what changed

Date: 2026-10-02. Scope: backend webhook, review pipeline, GitHub client, public API,
dashboard store.

The audit asked one question: what happens when someone tries Pairo on a real repo
and pushes on it? Most weaknesses were not crashes. They were **silent degradations**:
the review came back empty and looked like an all-clear.

Verification: 380 backend tests pass (351 before, 29 added), `ruff` and `mypy --strict`
are clean, the dashboard builds. Nothing was tested against the live GitHub API or the
production database.

## 1. A failed AI review looked like a clean one

**Weakness.** `LiteLLMReviewer.review` caught every exception and returned `[]`.
Invalid JSON from the model did the same. The posted review then said
"✅ Nothing to report". The same happened when the daily quota was reached. The call
had no timeout and no retry.

**Fix.**
- The reviewer now raises on a failed call or unreadable output.
- `ReviewPullRequest` catches it, keeps the built-in findings, and sets a `notice` on
  the `Review`. The PR shows "⚠️ AI review unavailable for this run" in place of ✅.
- The same mechanism reports "quota reached" and "large diff".
- `litellm.acompletion` gets `timeout=60` and `num_retries=2`.

Files: `infrastructure/llm/litellm_reviewer.py`, `application/review_pull_request.py`,
`domain/review.py`, `infrastructure/github/client.py`.

## 2. Unbounded diff sent to the model

**Weakness.** Every added line went into the prompt. A 20,000-line file meant a large
bill or a context overflow, which fell back to case 1.

**Fix.** The model receives at most `MAX_LLM_ADDED_LINES` (2000) added lines; the
review says so when the diff was cut. Built-in checks still run on everything.

File: `application/review_pull_request.py`.

## 3. Only the first 30 files of a PR were reviewed

**Weakness.** `get_pull_request_files` made one request with GitHub's default page
size (30). Larger PRs were partly reviewed, with no sign of it.

**Fix.** The client requests 100 per page and follows pages up to GitHub's 3000-file
limit. The compare endpoint used on `synchronize` was already fine: it returns up to
300 files in one response.

File: `infrastructure/github/client.py`.

## 4. One hallucinated line number lost the whole review

**Weakness.** GitHub rejects a review (422) if a single inline comment targets a line
outside the diff. Only code suggestions were validated, and the retry only ran when
suggestions were present. Otherwise nothing was posted.

**Fix.** `anchor_findings` turns any finding whose file or line is not an added line
into a general comment in the review body. The finding is kept; GitHub accepts it.

Files: `domain/suggestion.py`, `application/review_pull_request.py`.

## 5. GitHub calls had no explicit timeout or retry

**Weakness.** Ten call sites each built a bare `httpx.AsyncClient()`. A connection
blip dropped the review, visible only in the logs.

**Fix.** One `_client()` method sets a 15 s timeout and retries connection errors
twice. HTTP error statuses are still not retried.

File: `infrastructure/github/client.py`.

## 6. `@pairo ignore` accepted a reason of any length

**Weakness.** The reason could be as long as a GitHub comment (about 65,000
characters). It was stored and sent to two LLM calls (judge and writer).

**Fix.** `parse_command` truncates the reason to `MAX_REASON_CHARS` (500).

File: `domain/command.py`.

## 7. Anyone could dismiss a finding

**Weakness.** The decision was saved before the trust check, which only gated the
rule proposal. On a public repo, any commenter could silence a finding.

**Fix.** Dismissing now requires being an owner, member or collaborator, or the PR's
author. Other users are ignored: no decision, no reply. Proposing a `.pairo.md` rule
still requires a trusted association.

File: `api/webhook.py`.

## 8. The hidden marker could be forged

**Weakness.** Pairo identifies its findings by an HTML comment marker. The author of
the comment carrying the marker was never checked, so a user could paste a marker in
their own comment, then reply `@pairo ignore`, resolve the thread, or add 👎, and
write arbitrary decisions into the memory (and the dashboard stats).

**Fix.** A marker is trusted only in a comment written by a bot account. Checked in
all three paths: the command reply, the thread resolve webhook, and the GraphQL
thread sync at review time.

Limit: the check is "author is a bot", not "author is this app". Another bot posting
a look-alike marker would pass.

Files: `api/webhook.py`, `infrastructure/github/client.py`.

## 9. A PR could configure its own review

**Weakness.** `.pairo.yml` was read from the PR's head commit, while `.pairo.md` was
read from the base branch. A PR could add `ignore: ["*"]` and skip its own review.

**Fix.** `.pairo.yml` is now read from the base branch too. A config change applies
once merged. This is a behaviour change, documented in the README.

File: `application/review_pull_request.py`.

## 10. `.pairo.yml` values were trusted as typed

**Weakness.** No type validation: `ignore: 5` crashed the review. `language` and
`axes` were copied into the LLM prompt as free text, a direct prompt-injection path.

**Fix.** Each field falls back to its default on a wrong type. `axes` keeps only the
known axes, `language` must look like a language code (`fr`, `pt-BR`), list fields
keep only strings.

File: `domain/repo_config.py`.

## 11. Drafts marked "ready" were never reviewed

**Weakness.** Draft PRs are skipped, and `ready_for_review` was not a handled action.
A PR opened as draft got no review until the next push.

**Fix.** `ready_for_review` triggers a full review.

File: `api/webhook.py`.

## 12. Redeliveries were processed twice

**Weakness.** Delivery deduplication was an in-memory set, applied to `pull_request`
events only, never bounded, and lost on restart. A redelivered comment produced a
second bot reply; a redelivered PR event after a restart paid for and posted a second
review. `SqlReviewRepository.exists()` existed but was never called.

**Fix.** Deduplication covers every event type, the in-memory record is bounded to
10,000 ids, and `_run_review` checks the database before doing any work.

Limit: comment and thread events are still deduplicated in memory only.

File: `api/webhook.py`.

## 13. API parameters were unbounded

**Weakness.** `limit=100000000`, `limit=-1`, `offset=-1` or a 20-digit review id
reached the database and produced a 500 or a full table read.

**Fix.** `offset >= 0`, `1 <= limit <= 100`, review id within the 32-bit column
range. Out-of-range values return 422.

File: `api/reviews.py`.

## 14. The dashboard had no error handling

**Weakness.** Store fetches did not check `res.ok` or catch network errors. With the
backend asleep or failing, the page stayed blank or assigned an error body to the
state.

**Fix.** A `getJson` helper keeps the previous state on failure and sets
`store.error`, shown as a banner in the dashboard layout and cleared on navigation.

Files: `dashboard/src/stores/reviews.ts`, `dashboard/src/App.vue`.

## 15. The README promised a cache that was not wired

**Weakness.** `CachedLLMReviewer` and the `llm_cache` table existed and were tested,
but nothing instantiated the reviewer. Every review paid for an LLM call.

**Fix.** `_run_review` wraps the reviewer with the cache, using `LLM_CACHE_TTL_DAYS`.
The cache key now includes the review language. Failed LLM calls raise (see 1), so a
failure is never cached as an empty result. The fake provider is not cached.

Files: `api/webhook.py`, `infrastructure/llm/cached_reviewer.py`.

## 16. Dependencies did not match the code

**Weakness.** `ecologits` was declared and never imported. `pyyaml` was imported and
only present transitively.

**Fix.** `ecologits` removed, `pyyaml` declared, lockfile refreshed.

Files: `backend/pyproject.toml`, `backend/uv.lock`.

## Known weaknesses left open

These need a product decision or more than a small change.

- **No authentication on `/api/*`.** Reviews, findings and costs of every installed
  repo are readable by anyone with the URL. CORS does not stop a direct request.
  Fixing it means a login on the dashboard.
- **The daily quota is global**, across all installations, and does not count the
  LLM calls made by `@pairo ignore <reason>`. Heavy use on one repo switches the AI
  review off for all.
- **Background tasks run in the web process.** A restart during a review loses it.
  If the host cold-starts slower than GitHub's 10 s webhook timeout, the first
  delivery fails and GitHub does not retry on its own.
- **PR code enters the prompt as plain text.** A comment in the diff can try to steer
  the model. The reply path (`rule_classifier.py`) tags its input as untrusted; the
  review prompt does not.
- **`@pairo ignore` is matched anywhere in a reply**, including inside a quote.
- `domain/repo_config.py` imports `yaml`, against the "domain has no external
  dependency" rule.
