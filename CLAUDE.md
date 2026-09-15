# Pairo

AI-powered PR review tool. This repo is the admin dashboard (Vue 3 + TypeScript).

## Stack

- **Frontend:** Vue 3 (Composition API + `<script setup>`), TypeScript, Vite
- **State:** Pinia
- **Routing:** Vue Router
- **Styling:** Scoped CSS (no framework — keep it that way unless discussed)

## Commands

- `npm run dev` — start dev server
- `npm run build` — type-check + production build
- `npm run preview` — preview production build

## Conventions

- Use `<script setup lang="ts">` for all components
- Path alias: `@/` → `src/`
- Views go in `src/views/`, reusable components in `src/components/`
- Store modules in `src/stores/` (one file per store)
- Dark theme by default (#0f1117 bg, #e1e4e8 text, #7c6ef0 accent)
