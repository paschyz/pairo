# Pairo

AI-powered pull request reviewer. Installs as a GitHub App, reads every PR and posts inline review comments.

## Setup

1. Create a GitHub App with `pull_request` and `pull_request_review_comment` webhook events
2. Copy `.env.example` to `.env` and fill in your keys
3. `cd backend && make dev` — starts the API + webhook proxy
4. `cd dashboard && npm run dev` — starts the dashboard

## Pairo se souvient

Pairo tracks its own review comments and learns from your feedback. A rejected suggestion is never repeated on the same PR (unless the code changes).

### Commands

Reply to any Pairo comment with:

| Command | Effect |
|---------|--------|
| `@pairo ignore` | Reject this finding for this PR |
| `@pairo ignore <reason>` | Same, with a reason recorded |
| `@pairo valid` | Cancel a previous rejection |

Pairo confirms with a short reply in the thread.

### Other signals

- **Thumbs-down reaction** on a Pairo comment = rejection
- **Resolved thread** without code change = rejection
- **Code changed** since rejection = finding becomes eligible again

### How it works

Each Pairo comment contains an invisible HTML marker with a content-based fingerprint. The fingerprint is computed from the code context (not line numbers), so moving code around without changing it keeps the same identity.

Before posting a new review, Pairo checks all its previous comments on the PR, collects signals (commands, reactions, resolved threads), and filters out findings that were already rejected or posted.

### Persistent rules

If a category (e.g. `crafts.naming`) is rejected on 3+ PRs in the same repo, Pairo suggests adding it to `.pairo.yml`:

```yaml
ignore_categories: ["crafts.naming"]
```

Wildcards work: `crafts.*` ignores all craftsmanship findings. The decision stays human, versioned, and visible in the repo.

### Configuration (.pairo.yml)

```yaml
memory:
  enabled: true              # default
  classify_replies: false    # LLM classification of free-text replies (off by default)
ignore_categories: []        # e.g. ["crafts.naming", "eco.*"]
```

### Deterministic cache

Identical code + same config + same prompt version + same model = cached result, no LLM call. The cache invalidates automatically when prompts, model, or config change. TTL: `LLM_CACHE_TTL_DAYS` (default 30).

## API

| Endpoint | Description |
|----------|-------------|
| `POST /webhook` | GitHub webhook handler |
| `GET /health` | Health check |
| `GET /api/reviews` | List reviews (paginated) |
| `GET /api/reviews/{id}` | Review detail with findings |
| `GET /api/stats` | Aggregate stats |
| `GET /api/stats/memory` | Memory stats (rejections by signal/category) |
