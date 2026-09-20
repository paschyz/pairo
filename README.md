
<div align="center">

<img src="dashboard/src/assets/pairo.png" alt="Pairo logo" width="160">

# Pairo

**AI-Powered PR Reviewer That Learns From Your Feedback**

[![GitHub last commit](https://img.shields.io/github/last-commit/paschyz/pairo/main?style=for-the-badge)](https://github.com/paschyz/pairo/commits/main)
[![License](https://img.shields.io/github/license/paschyz/pairo?style=for-the-badge)](https://github.com/paschyz/pairo/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Vue](https://img.shields.io/badge/vue-3-4FC08D?style=for-the-badge&logo=vue.js&logoColor=white)](https://vuejs.org)

</div>

---

Pairo is an open-source GitHub App that reviews your pull requests using AI and **remembers your feedback**. Reject a suggestion once — Pairo won't repeat it. Over time, it adapts to your team's preferences and coding standards.

## Table of Contents

- [Why Pairo?](#why-pairo)
- [Features](#features)
- [See It in Action](#see-it-in-action)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
- [Architecture](#architecture)
- [Data Privacy](#data-privacy)
- [Contributing](#contributing)

## Why Pairo?

Most AI code reviewers treat every PR as a blank slate. They repeat the same irrelevant suggestions, ignore your team's conventions, and generate noise instead of signal.

Pairo is different:

- **It learns.** Reject a finding and it's gone — not just for that PR, but for similar code across your repo.
- **It's transparent.** Every decision is tracked, visible, and reversible. No black box.
- **It's fast.** Deterministic caching means identical code gets instant results — no redundant LLM calls.
- **It's yours.** Fully open-source, self-hosted. Your code never leaves your infrastructure.

## Features

| Feature | Description |
|---------|-------------|
| **AI Review** | Posts inline review comments on every PR with actionable findings |
| **Memory System** | Tracks rejected suggestions and never repeats them |
| **Feedback Commands** | Reply `@pairo ignore` or `@pairo valid` to control findings |
| **Signal Detection** | Picks up thumbs-down reactions, resolved threads, and explicit commands |
| **Content Fingerprinting** | Identifies findings by code content, not line numbers — survives rebases |
| **Persistent Rules** | Frequently rejected categories auto-suggest `.pairo.yml` rules |
| **Deterministic Cache** | Same code + config + model = cached result, zero LLM cost |
| **Dashboard** | Real-time analytics: reviews, findings, token usage, memory stats |
| **Category Suppression** | Suppress entire finding categories via config (wildcards supported) |

## See It in Action

### PR Review

Pairo posts inline comments with categorized findings on every pull request:

<img width="1250" height="819" alt="image" src="https://github.com/user-attachments/assets/647aa160-a430-4c0a-8b11-528c3431fffe" />
<img width="770" height="310" alt="image" src="https://github.com/user-attachments/assets/7e658376-2630-4cb3-a449-78e5d4218567" />
<img width="768" height="308" alt="image" src="https://github.com/user-attachments/assets/e0452e91-1e90-45d4-9d91-e9866fea58db" />
<img width="769" height="308" alt="image" src="https://github.com/user-attachments/assets/e38c1c78-f151-472e-98d8-b30b816017dd" />

### Feedback Loop

```
You:    @pairo ignore — naming is fine for internal utils
Pairo:  ✅ Got it. Finding ignored for this PR.
```

Next review, that suggestion won't appear.

### Dashboard

The analytics dashboard shows review history, finding distribution, token usage, and memory stats — all in real time.

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- A [GitHub App](https://docs.github.com/en/developers/apps/creating-a-github-app) with `pull_request` and `pull_request_review_comment` webhook events
- An LLM API key (Gemini by default)

### 1. Clone & Configure

```bash
git clone https://github.com/paschyz/pairo.git
cd pairo
cp backend/.env.example backend/.env
# Fill in: GITHUB_APP_ID, GITHUB_PRIVATE_KEY_PATH, GEMINI_API_KEY, DATABASE_URL
```

### 2. Start the Backend

```bash
cd backend
make dev    # Starts FastAPI + smee webhook proxy
```

### 3. Start the Dashboard

```bash
cd dashboard
npm install
npm run dev
```

### 4. Point Your GitHub App

Set your GitHub App's webhook URL to your backend (use [smee.io](https://smee.io) for local development).

## Configuration

### `.pairo.yml` (per-repo)

Drop a `.pairo.yml` at the root of any repo where Pairo is installed:

```yaml
memory:
  enabled: true               # Track and learn from feedback (default: true)
  classify_replies: false     # Use LLM to classify free-text replies (default: false)

ignore_categories:            # Suppress finding categories
  - crafts.naming
  - eco.*                     # Wildcards supported
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_APP_ID` | Your GitHub App ID | — |
| `GITHUB_PRIVATE_KEY` | PEM key contents (or use `_PATH`) | — |
| `GEMINI_API_KEY` | Google Gemini API key | — |
| `DATABASE_URL` | PostgreSQL connection string | `sqlite:///./pairo.db` |
| `LLM_PROVIDER` | `gemini` or `fake` (for tests) | `gemini` |
| `LLM_CACHE_TTL_DAYS` | Cache expiration | `30` |

## How It Works

```
PR Opened/Updated
       │
       ▼
  ┌─────────┐    ┌──────────┐    ┌─────────────┐
  │  GitHub  │───▶│  Webhook │───▶│  Check Cache │
  │ Webhook  │    │  Handler │    │  (hit? skip) │
  └─────────┘    └──────────┘    └──────┬───────┘
                                        │ miss
                                        ▼
                                 ┌─────────────┐
                                 │  LLM Review  │
                                 │  (Gemini)    │
                                 └──────┬───────┘
                                        │
                                        ▼
                                 ┌─────────────┐
                                 │   Filter vs  │
                                 │   Memory DB  │──▶ Skip rejected findings
                                 └──────┬───────┘
                                        │
                                        ▼
                                 ┌─────────────┐
                                 │ Post Review  │
                                 │ + Markers    │──▶ Invisible fingerprint per comment
                                 └─────────────┘
```

**Memory loop:** When you reject a finding (`@pairo ignore`, 👎, or resolve the thread), Pairo records the decision. On the next review, rejected findings are filtered out before posting.

**Fingerprinting:** Each finding is identified by a normalized hash of its code context — not line numbers. Move code around, rebase, reformat — the fingerprint stays stable.

## Architecture

Pairo is a monorepo with a hexagonal backend and a Vue 3 dashboard.

```
pairo/
├── backend/                # Python 3.12 + FastAPI
│   └── src/pairo/
│       ├── domain/         # Pure Python — no external deps
│       ├── application/    # Use cases, orchestration
│       ├── infrastructure/ # GitHub client, Gemini, SQLAlchemy
│       └── api/            # FastAPI routes
├── dashboard/              # Vue 3 + TypeScript + Vite
│   └── src/
│       ├── views/          # Dashboard, Reviews, Detail
│       ├── stores/         # Pinia state management
│       └── components/     # Reusable UI components
```

**Key design decisions:**
- Domain layer has zero external dependencies
- Ports & adapters for LLM and GitHub — swap providers without touching business logic
- Content-based fingerprinting over line-number tracking
- Free signals (reactions, commands) prioritized over LLM classification

## Data Privacy

- **Self-hosted.** Your code stays on your infrastructure.
- **No telemetry.** Pairo sends nothing home.
- **LLM calls are yours.** You control which LLM provider sees your code and under what terms.
- **Memory is local.** All decisions and cached results live in your database.

## Contributing

Contributions are welcome! The codebase follows strict conventions:

```bash
cd backend
make test     # pytest with coverage
make lint     # ruff + mypy (strict)

cd dashboard
npm run build # type-check + vite build
```

- **Backend:** TDD (test first), hexagonal architecture, strict mypy
- **Frontend:** Vue 3 Composition API, `<script setup>`, scoped CSS
- Domain layer must never import from infrastructure

---

<div align="center">
  <sub>Built with Gemini, FastAPI, Vue 3, and a healthy dislike for noisy code reviews.</sub>
</div>
