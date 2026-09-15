# Pairo

AI-powered PR review GitHub App. Monorepo: `dashboard/` (Vue 3) + `backend/` (Python/FastAPI).

## Dashboard (`dashboard/`)

### Stack

- **Frontend:** Vue 3 (Composition API + `<script setup>`), TypeScript, Vite
- **State:** Pinia
- **Routing:** Vue Router
- **Styling:** Scoped CSS (no framework — keep it that way unless discussed)

### Commands

```sh
cd dashboard
npm run dev       # start dev server
npm run build     # type-check + production build
npm run preview   # preview production build
```

### Conventions

- Use `<script setup lang="ts">` for all components
- Path alias: `@/` → `src/`
- Views go in `src/views/`, reusable components in `src/components/`
- Store modules in `src/stores/` (one file per store)
- Dark theme by default (#0f1117 bg, #e1e4e8 text, #7c6ef0 accent)

## Backend (`backend/`)

### Stack

- **Runtime:** Python 3.12, FastAPI, Pydantic v2, httpx (async)
- **LLM:** `google-genai` SDK (Gemini), behind a `LLMReviewer` port
- **DB:** SQLAlchemy 2 + Alembic (SQLite local, PostgreSQL prod)
- **Auth:** `pyjwt[crypto]` for GitHub App JWT
- **Tooling:** uv, ruff, mypy (strict), pytest + pytest-asyncio + respx

### Commands

```sh
cd backend
make dev      # uvicorn + smee-client in parallel
make test     # pytest with coverage
make lint     # ruff check + format + mypy
make format   # auto-fix ruff issues
make migrate  # alembic upgrade head
```

### Architecture (hexagonal)

```
src/pairo/
  domain/          # pure Python, no external deps
  application/     # use cases, orchestrates domain via ports
  infrastructure/  # GitHub client, Gemini adapter, SQLAlchemy repos
  api/             # FastAPI routes (webhook, stats, health)
  config.py        # pydantic-settings, reads env vars
  app.py           # FastAPI entry point
```

### Conventions

- `domain/` never imports from `infrastructure/`, `api/`, or external libs
- Use cases receive ports via dependency injection
- No business logic in FastAPI routes
- `LLM_PROVIDER=fake` for tests and dev without API key
- TDD: test first, then implementation, then refactor
