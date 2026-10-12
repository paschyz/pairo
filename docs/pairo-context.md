# Pairo: project context

This file describes the Pairo project as it exists in the code on 2026-10-02
(branch `feat/dashboard-kpis-showreel`). It is written to be given to an LLM as
background. Where the README or older docs disagree with the code, this file follows
the code and says so in section 12.

## 1. What Pairo is

Pairo is an open-source, self-hosted GitHub App that reviews pull requests with an LLM
and remembers the feedback it gets.

- On each pull request it posts one GitHub review: inline comments on added lines, plus
  a summary.
- It reviews along three axes:
  - `crafts`: naming, long functions, duplication, dead code, readability.
  - `eco`: N+1 queries, missing pagination, heavy dependencies, unnecessary computation.
  - `a11y`: missing `alt`, low contrast, non-semantic elements, keyboard navigation.
- Findings come from two sources: `rule` (deterministic checks written in Python) and
  `llm` (the model).
- When a developer dismisses a finding, Pairo records it and does not post that finding
  again on the same PR.
- When the dismissal gives a reason that states a project-wide convention, Pairo opens a
  pull request adding that convention as a rule to `.pairo.md`. Once merged, the rule is
  given to the LLM on every later review of that repo.
- A web dashboard shows reviews, findings, token usage, cost and memory statistics.

The product's pitch: most AI reviewers repeat the same irrelevant comments; Pairo is
told once and does not repeat it.

## 2. Repository layout

```
pairo/
  backend/      Python 3.12, FastAPI. The GitHub App and the JSON API.
  dashboard/    Vue 3 + TypeScript + Vite. Landing page and analytics dashboard.
  video/        Remotion project that renders a 20-second showreel with a generated score.
  docs/         ADR, hardening report, design specs, this file.
  .github/workflows/backend.yml   CI for the backend.
```

## 3. Tech stack

| Part | Stack |
| --- | --- |
| Backend runtime | Python 3.12, FastAPI, Pydantic v2, pydantic-settings, httpx (async), uvicorn |
| LLM access | `litellm` (Gemini, OpenRouter or any litellm model), behind the `LLMReviewer` port |
| Judge model | "Jev", called through OpenRouter's Decisions API (`https://openrouter.ai/api/alpha/decisions`) with plain httpx |
| Database | SQLAlchemy 2 + Alembic. SQLite locally, Supabase PostgreSQL in production |
| GitHub auth | `pyjwt[crypto]`: App JWT (RS256), exchanged for an installation token |
| Backend tooling | uv, ruff, mypy (strict), pytest, pytest-asyncio, respx |
| Dashboard | Vue 3 (Composition API, `<script setup lang="ts">`), Pinia, Vue Router, Vite, scoped CSS, no CSS framework |
| Video | Remotion (React/TypeScript) for picture, one Python script for the music |

## 4. Backend architecture (hexagonal)

```
backend/src/pairo/
  domain/          Pure logic and the ports (Protocols). No I/O.
  application/     Use cases. Receive ports by constructor injection.
  infrastructure/  Adapters: GitHub client, LLM adapters, SQLAlchemy repositories.
  api/             FastAPI routes. Build the adapters and call the use cases.
  config.py        Settings read from environment variables.
  app.py           FastAPI app: CORS, routers, GET /health.
```

Rules of the architecture:

- `domain/` never imports from `infrastructure/` or `api/`.
- Use cases depend on ports, not on concrete adapters.
- Routes hold no business logic.
- The composition root is `api/webhook.py`: it builds `GitHubClient`, the LLM reviewer,
  the cache wrapper and the repositories for each webhook, then runs a use case.

### 4.1 Domain (`domain/`)

| File | Role |
| --- | --- |
| `finding.py` | `Finding` (axis, file, line, issue, suggestion, source, category, code_suggestion), `Axis`, `Source`, `CodeSuggestion`. Lenient parsers for untrusted LLM/cache data. |
| `review.py` | `Review`: findings plus model, token counts, PR identity, `memory_filtered`, `memory_summary`, `notice` (why a review is partial). |
| `decision.py` | `FindingDecision` with `DecisionStatus` (`posted`, `rejected`, `accepted`, `resolved_with_change`) and `DecisionSignal` (`command`, `reaction`, `resolved_unchanged`, `reply_llm`). |
| `ports.py` | Protocols: `CodeHost`, `LLMReviewer`, `RuleJudge`, `RuleWriter`, `ReviewRepository`, `DecisionRepository`. Also `FileDiff` (path, added lines, status). |
| `diff.py` | `parse_patch`: unified diff to `AddedLine(number, content)` with new-file line numbers. |
| `fingerprint.py` | `compute_fingerprint` and `fingerprint_for(finding)`: 16 hex chars of a SHA-256. |
| `marker.py` | Hidden HTML marker in each review comment: `<!-- pairo:fp=<fingerprint>;axis=<axis>;cat=<category>;v=1 -->`. |
| `command.py` | Parses `@pairo ignore [reason]`. The reason is cut to 500 characters. `ignore` is the only command. |
| `filter_findings.py` | Drops findings whose fingerprint has a suppressing decision; builds the "previously dismissed" summary line. |
| `decision_rebuild.py` | Rebuilds decisions from GitHub comments: resolved thread or 👎 reaction means rejected. |
| `repo_config.py` | Parses `.pairo.yml` into `RepoConfig`, falling back to defaults on wrong types. |
| `context_rule.py` | `.pairo.md` logic: trusted associations, `RuleVerdict`, `merge_rule` (dedupe, 280 chars per rule, 8000 chars per file). |
| `suggestion.py` | `anchor_findings` and `sanitize_suggestions`: keep GitHub from rejecting a review because of a bad line number or suggestion range. |
| `cache_key.py` | SHA-256 cache key over files, axes, config, prompt version and model. |
| `classify_reply.py` | Schema and parser for LLM classification of free-text replies. |
| `rules/alt.py` | Deterministic check: `<img>` without `alt` in `.html`, `.jsx`, `.tsx`, `.vue`. |
| `rules/contrast.py` | Deterministic check: `color` and `background` hex values on one line with a WCAG contrast ratio under 4.5:1, in `.css`, `.scss`, `.less`, `.vue`. |
| `rules/image_size.py` | Deterministic check: image file larger than `max_image_kb`. |

### 4.2 Application (`application/`)

- `review_pull_request.py`: `ReviewPullRequest.execute(...)`, the review pipeline
  (section 5).
- `propose_context_rule.py`: `ProposeContextRule.execute(...)`, turns a dismissal reason
  into a pull request on `.pairo.md` (section 6.2).

### 4.3 Infrastructure (`infrastructure/`)

| File | Role |
| --- | --- |
| `github/auth.py` | `GitHubAppAuth`: signs the App JWT, fetches and caches installation tokens. |
| `github/client.py` | `GitHubClient`, the `CodeHost` adapter. REST for files, compare, file contents, reviews, comments, reactions; GraphQL for review threads. 15 s timeout, 2 retries on connection errors. Skips lock files, minified files, `vendor/` and `node_modules/`. Renders review comments and the review body. |
| `llm/factory.py` | `create_reviewer`, `create_judge`, `create_rule_filter`. Providers: `fake`, `gemini`, `openrouter`, `litellm`. One rate limiter per provider, shared per process. |
| `llm/litellm_reviewer.py` | `LiteLLMReviewer`: review, `judge_rule`, `write_rule`. 60 s timeout, 2 retries. Raises on a failed call or unreadable JSON. |
| `llm/prompt.py` | `build_prompt` and `PROMPT_VERSION` (currently `"6"`). |
| `llm/cached_reviewer.py` | `CachedLLMReviewer`: wraps a reviewer with the deterministic cache. |
| `llm/jev_judge.py` | `JevJudge`: `judge_rule` and `excluded_by_rules` through the Decisions API. |
| `llm/rule_classifier.py` | Prompts and strict Pydantic parsers for the judge and writer when a chat model does the job. Marks its inputs as untrusted data. |
| `llm/pricing.py` | `cost_usd`: token cost from the price table shipped with litellm, computed at read time. |
| `llm/rate_limiter.py` | Sliding 60-second window limiter (requests per minute). |
| `llm/fake.py` | `FakeLLMReviewer`: one fixed finding per file; no network. Used in tests and local dev. |
| `persistence/models.py` | Tables (section 8). |
| `persistence/repository.py` | `SqlReviewRepository`: save, exists, get, list, per-PR history, daily count, stats, KPIs. |
| `persistence/decision_repo.py` | `SqlDecisionRepository`: upsert and read decisions, memory stats. |
| `persistence/finding_cache.py` | `SqlFindingCache`: get/put with a TTL. |
| `persistence/engine.py` | Lazy engine and session factory from `DATABASE_URL`. |

### 4.4 API (`api/`)

| Endpoint | Purpose |
| --- | --- |
| `POST /webhook` | GitHub webhook entry point (section 5 and 6). |
| `GET /health` | Health check. |
| `GET /api/reviews?offset=0&limit=20` | Paginated review list. `limit` is 1 to 100. |
| `GET /api/reviews/{id}` | One review with its findings and the review history of the same PR. |
| `GET /api/stats` | Totals: reviews, findings, input and output tokens. |
| `GET /api/stats/kpis` | Cost, PR count, clean reviews, median minutes to first review, breakdowns by repo, model, axis and source, daily activity. |
| `GET /api/stats/memory` | Rejections by signal, decisions by status. |

The `/api/*` endpoints have no authentication.

## 5. Flow: reviewing a pull request

1. GitHub sends a `pull_request` event to `POST /webhook`.
2. The route checks the HMAC signature (`X-Hub-Signature-256` against
   `GITHUB_WEBHOOK_SECRET`). An invalid or missing signature returns 401.
3. Redeliveries are dropped: the `X-GitHub-Delivery` id is kept in an in-memory,
   bounded record (10,000 ids), and reviews are also checked against the database.
4. Only the actions `opened`, `synchronize`, `reopened` and `ready_for_review` are
   handled. Draft PRs are skipped.
5. The route answers 202 and runs the review as a FastAPI background task in the same
   process.
6. The task gets an installation token and runs `ReviewPullRequest.execute`:
   1. Read `.pairo.yml` from the PR's **base branch** and parse it.
   2. Get the files. On `synchronize` with a `before` SHA, only the changes between
      the previous head and the new head are fetched (compare API); otherwise all files
      of the PR.
   3. Remove files matching the config's `ignore` patterns.
   4. Run the deterministic checks (`alt`, `contrast`) on added lines when the `a11y`
      axis is enabled.
   5. Check the daily quota (`DAILY_REVIEW_QUOTA`, counted across all repos). When it
      is reached, the LLM is skipped and the review says so.
   6. Read `.pairo.md` from the base branch (first 8000 characters): the project rules.
   7. If Jev is configured, ask it which deterministic findings the project rules
      exclude, and drop those. If Jev fails, nothing is dropped.
   8. Call the LLM with at most 2000 added lines, the axes, the language, the project
      rules and the findings already detected (so it does not duplicate them). The
      cache wrapper returns stored findings when the key matches (section 7).
   9. If the LLM call fails, keep the deterministic findings and add a notice to the
      review; the review never reads as "nothing to report" after a failure.
   10. `anchor_findings`: a finding whose line is not an added line becomes a general
       comment in the review body. `sanitize_suggestions`: a code suggestion that does
       not map onto added lines is removed; the finding is kept.
   11. Memory filtering (section 6.1).
   12. Post one GitHub review with event `COMMENT`. Each inline comment has the axis
       emoji and name, the issue, the suggestion, an optional native GitHub
       ` ```suggestion ` block, and the hidden marker. The body has counts per axis,
       the memory line and any notice. If GitHub answers 422 and suggestions were
       present, the review is posted again without suggestions.
   13. Save the review and its findings to the database.

The LLM prompt asks for a JSON array of objects with `axis`, `file`, `line`, `issue`,
`suggestion` and an optional `code_suggestion` (`replacement`, `end_line`).

## 6. The memory system

### 6.1 Dismissing a finding

There are three ways to dismiss a finding. All of them identify the finding by the
marker in Pairo's comment, and a marker is trusted only when the comment's author is a
bot account.

| Signal | How it is detected |
| --- | --- |
| `@pairo ignore [reason]` replied to a Pairo comment | `pull_request_review_comment` webhook, action `created` |
| Resolving the conversation | `pull_request_review_thread` webhook, action `resolved`. `unresolved` undoes a rejection that came from a resolve. |
| 👎 reaction on the comment | Read at the next review, when Pairo fetches the PR's threads and reactions |

Who may use `@pairo ignore`: a repo owner, member or collaborator, or the PR's author.
Anyone else is ignored without a reply.

A decision is stored with the key (repo, PR number, fingerprint). At each review, Pairo
syncs resolved threads and 👎 reactions from GitHub into the database, loads the PR's
decisions, and drops the new findings whose fingerprint matches. The review body then
says how many previously dismissed comments were not reposted.

Decisions are scoped to one PR. What carries across PRs is the `.pairo.md` rule below.

### 6.2 Turning a reason into a project rule

When `@pairo ignore` has a reason and the author is an owner, member or collaborator:

1. `.pairo.yml` on the default branch must allow it (`context.propose_rules`, default
   true).
2. A judge decides whether the reason states a durable, project-wide convention
   ("we don't use Redis in this project") or a one-off exception. The judge is Jev when
   `LLM_PROVIDER=openrouter` and `LLM_MODEL_JUDGE` is set; otherwise the chat model.
   The verdict must have `persist=true` and a confidence of at least
   `CONTEXT_RULE_THRESHOLD` (default 0.5).
3. The default chat model writes the rule as one short sentence.
4. The rule is merged into `.pairo.md`: not added if it duplicates an existing line or
   would push the file past 8000 characters.
5. Pairo commits the file on the branch `pairo/context` and opens a pull request, or
   adds to that pull request if it is already open. Nothing is pushed to the default
   branch.
6. Pairo replies in the thread: "👍 Ignored on this PR." plus the link to the rule
   pull request when one was proposed.

The rule takes effect once a human merges that pull request, because reviews read
`.pairo.md` from the base branch. A failure in this flow never undoes the dismissal.

### 6.3 Fingerprint

`fingerprint_for(finding)` hashes the axis, the file path and the finding's issue text
(plus a rule id for deterministic findings) and keeps 16 hex characters. Line numbers
are not part of it. The same function is used for the marker and for filtering.

## 7. Deterministic LLM cache

`CachedLLMReviewer` computes a SHA-256 key from: the added lines of each file, the
axes, the review language, the `.pairo.md` content, `PROMPT_VERSION` and the model
name. On a hit, the stored findings are returned and no LLM call is made (token counts
for that review are 0). Entries expire after `LLM_CACHE_TTL_DAYS` (default 30). A
failed LLM call raises, so a failure is never cached. The fake provider is not cached.
Changing a prompt requires incrementing `PROMPT_VERSION`.

## 8. Database

| Table | Content |
| --- | --- |
| `reviews` | One row per posted review: unique `delivery_id`, owner, repo, PR number, head SHA, model, input and output tokens, `co2_g`, `created_at`, `pr_created_at`. |
| `findings` | The findings of a review: axis, file, line, issue, suggestion, source. |
| `finding_decisions` | The memory: repo, PR number, fingerprint (unique together), axis, category, status, signal, reason, decided_by, GitHub comment id, timestamps. |
| `llm_cache` | Cache key, findings as JSON, token counts, `created_at`. |

Migrations are in `backend/migrations/versions/` (Alembic). Datetimes are stored as
naive UTC.

## 9. Configuration

### 9.1 Per repository: `.pairo.yml` (read from the PR's base branch)

```yaml
axes: [crafts, eco, a11y]     # which axes to review (default: all three)
language: en                  # language of the review text, e.g. fr, pt-BR
ignore: ["docs/*"]            # fnmatch patterns of files to skip
max_image_kb: 200
ignore_categories: ["eco.*"]
memory:
  enabled: true
  classify_replies: false
context:
  propose_rules: true         # allow rule pull requests on .pairo.md
```

Section 12 lists which of these keys the review pipeline does not read yet.

### 9.2 Per repository: `.pairo.md`

Free-text project rules, one per line under the header `# Pairo context`. Written by
Pairo's rule pull requests or by hand. At most 8000 characters are read.

### 9.3 Backend environment variables

| Variable | Default | Meaning |
| --- | --- | --- |
| `GITHUB_APP_ID` | `0` | GitHub App id |
| `GITHUB_PRIVATE_KEY` / `GITHUB_PRIVATE_KEY_PATH` | empty / `./pairo.private-key.pem` | App private key, inline or as a file |
| `GITHUB_WEBHOOK_SECRET` | empty | Webhook HMAC secret. Empty means every webhook is rejected. |
| `LLM_PROVIDER` | `fake` | `fake`, `gemini`, `openrouter` or `litellm` |
| `LLM_API_KEY` | empty | Provider key. `GEMINI_API_KEY` is used instead when the provider is `gemini` and this is empty. |
| `LLM_MODEL_DEFAULT` | empty | Review model. Defaults: `gemini-2.0-flash` (gemini), `anthropic/claude-haiku-4.5` (openrouter). |
| `LLM_MODEL_JUDGE` | empty | Jev model for rule judging and rule filtering (OpenRouter only) |
| `LLM_RPM_LIMIT` | `15` | LLM requests per minute |
| `DAILY_REVIEW_QUOTA` | `50` | Reviews per day before the LLM is skipped |
| `LLM_CACHE_TTL_DAYS` | `30` | Cache expiry |
| `CONTEXT_RULE_THRESHOLD` | `0.5` | Minimum judge confidence to propose a rule |
| `DATABASE_URL` | `sqlite:///./pairo.db` | Database connection |
| `DASHBOARD_ORIGIN` | `http://localhost:3000` | Allowed CORS origin |
| `SMEE_URL` | empty | smee.io channel for local webhook forwarding |

The GitHub App needs the webhook events `pull_request`, `pull_request_review_comment`
and `pull_request_review_thread`, and the permissions Pull requests: write and
Contents: write (the last one for the `.pairo.md` pull requests).

## 10. Dashboard (`dashboard/`)

| Route | View | Content |
| --- | --- | --- |
| `/` | `HomeView.vue` | Public landing page with the mascot. The Demo button opens `/pairo-showreel-1080p.mp4`. |
| `/dashboard` | `DashboardView.vue` | KPI groups, breakdowns, recent reviews |
| `/reviews` | `ReviewsView.vue` | Review list |
| `/reviews/:id` | `ReviewDetailView.vue` | One review with its findings and PR history |

- One Pinia store, `src/stores/reviews.ts`, calls the five `/api/*` endpoints. On a
  failed request it keeps the previous state and sets `error`, which `App.vue` shows as
  a banner.
- `App.vue` picks the layout from the route's `meta.layout`.
- Dark theme: background `#0f1117`, text `#e1e4e8`, accent `#7c6ef0`.
- Conventions: `<script setup lang="ts">`, alias `@/` for `src/`, views in `src/views/`,
  reusable components in `src/components/`, one file per store, scoped CSS only.

## 11. Deployment, commands and CI

- **Dashboard**: Vercel. `dashboard/vercel.json` rewrites `/api/*` and `/health` to the
  backend at `https://pairo-tk2g.onrender.com` and everything else to `index.html`.
- **Backend**: Render, Docker (`backend/Dockerfile`, `backend/render.yaml`). The
  container runs `alembic upgrade head`, then uvicorn on `$PORT` (8000). One process.
- **Database**: Supabase PostgreSQL in production.
- **Local webhooks**: smee.io forwards GitHub events to `localhost:8000/webhook`.

```sh
cd backend
make dev      # uvicorn with reload + smee-client
make test     # pytest with coverage
make lint     # ruff check, ruff format --check, mypy
make format   # ruff auto-fix
make migrate  # alembic upgrade head

cd dashboard
npm run dev
npm run build # vue-tsc + vite build
```

CI (`.github/workflows/backend.yml`) runs ruff, mypy and pytest on backend changes with
`LLM_PROVIDER=fake`. The backend is developed test-first; tests mirror the source tree
under `backend/tests/` and use respx to mock GitHub.

### Showreel (`video/`)

A 20-second, 1080p, 60 fps film. `score/score.py` composes and renders the music and
writes `src/timeline.json`; the Remotion scenes (`Noise`, `TellItOnce`, `NeverBack`,
`Blitz`, `Lockup`) read every timing from that file. `npm run render` writes
`video/out/pairo-showreel-1080p.mp4`, which is copied by hand to `dashboard/public/`.

## 12. Gaps between the docs and the code

Things an LLM reading the README or `CLAUDE.md` would get wrong:

- **LLM SDK.** `CLAUDE.md` names the `google-genai` SDK and the README says "Gemini".
  The code uses `litellm`; Gemini is one of four providers, and the default provider in
  `config.py` is `fake`.
- **Config keys that are parsed but not used by the review pipeline:**
  `ignore_categories`, `memory.enabled`, `memory.classify_replies`, `max_image_kb`.
- **Finding categories.** `Finding.category` is always empty for LLM and rule findings,
  and the marker is written with an empty `cat`. Category-based features therefore have
  nothing to match on.
- **Domain code with no caller:** `rules/image_size.py` (`check_image_size`),
  `suggest_persistent_rule` in `filter_findings.py` (the "dismissed on 3 PRs, add it to
  `.pairo.yml`" hint), `classify_reply.py` (LLM classification of free-text replies),
  and `DecisionRepository.count_rejected_prs_by_category`.
- **Fingerprint.** The README and the ADR describe a fingerprint built from normalized
  code context. `compute_fingerprint` supports that, but `fingerprint_for` currently
  passes the finding's issue text as the context. An LLM that words the same issue
  differently produces a different fingerprint.
- **Memory scope.** The README says a rejected finding is gone "for similar code across
  your repo". Decisions are stored and applied per PR; only merged `.pairo.md` rules
  apply repo-wide.
- **`@pairo valid`** is mentioned in the ADR. Only `ignore` exists.
- **CO₂.** `Review.co2_g` and the `co2_g` column exist, and the review body can print
  it, but nothing sets it.
- **`LLM_MODEL_LARGE`** is a setting that nothing reads.
- **`domain/repo_config.py` imports `yaml`**, which breaks the rule that the domain has
  no external dependency.

## 13. Known limits

From `docs/hardening-2026-10-02.md`, still open:

- No authentication on `/api/*`: anyone with the URL can read reviews, findings and
  costs.
- The daily quota is global across installations and does not count the LLM calls made
  by `@pairo ignore <reason>`.
- Reviews run as background tasks in the web process: a restart during a review loses
  it, and there is no queue.
- Per-process state: the delivery record, the rate limiter and the installation token
  cache do not work across several workers.
- PR code is put in the review prompt as plain text, so a comment in a diff can try to
  steer the model. The rule judge and writer prompts mark their input as untrusted; the
  review prompt does not.
- `@pairo ignore` is matched anywhere in a reply, including inside a quote.
- The marker check is "written by a bot", not "written by this app".
- Cost is computed at read time from litellm's current price table, so historical
  costs change when prices change.

## 14. Further reading in the repo

- `README.md`: user-facing presentation and setup.
- `CLAUDE.md`: coding conventions for the repo.
- `docs/adr/001-memory-architecture.md`: why the memory is built on fingerprints,
  deterministic signals, markers and a versioned cache.
- `docs/hardening-2026-10-02.md`: 16 weaknesses fixed and those left open.
- `docs/superpowers/specs/`: design specs for the `.pairo.md` rule proposal and the
  showreel.
- `video/README.md`: how the showreel and its score are built.
