<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useReviewStore } from '@/stores/reviews'
import { formatDateTime, timeAgo } from '@/utils/time'

const store = useReviewStore()

const refreshing = ref(false)
const loaded = ref(false)

async function refresh() {
  refreshing.value = true
  try {
    await Promise.all([
      store.fetchStats(),
      store.fetchMemoryStats(),
      store.fetchKpis(),
      store.fetchReviews(0, 5),
    ])
  } finally {
    refreshing.value = false
    loaded.value = true
  }
}

onMounted(() => {
  refresh();
});

const signalLabels: Record<string, string> = {
  command: '@pairo ignore',
  reaction: '👎 reaction',
  resolved_unchanged: 'Resolved thread',
  reply_llm: 'Reply',
}

const axisLabels: Record<string, string> = {
  crafts: 'Crafts',
  eco: 'Eco-design',
  a11y: 'Accessibility',
}

const sourceLabels: Record<string, string> = {
  llm: 'LLM',
  rule: 'Static rule',
}

const NONE = '—'
const int = new Intl.NumberFormat('en')
const decimal = new Intl.NumberFormat('en', { maximumFractionDigits: 1 })
const compact = new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 })
const percent = new Intl.NumberFormat('en', { style: 'percent', maximumFractionDigits: 0 })
const dollars = new Intl.NumberFormat('en', { style: 'currency', currency: 'USD' })
const cents = new Intl.NumberFormat('en', { style: 'currency', currency: 'USD', maximumFractionDigits: 4 })

const div = (a: number | null, b: number) => (a === null || !b ? null : a / b)
const show = (v: number | null, f: Intl.NumberFormat) => (v === null ? NONE : f.format(v))
const plural = (n: number, word: string) => `${int.format(n)} ${word}${n === 1 ? '' : 's'}`
const sum = (values: number[]) => values.reduce((a, b) => a + b, 0)

function usd(v: number | null): string {
  if (v === null) return NONE
  if (v > 0 && v < 0.0001) return '<$0.0001'
  return (v < 1 ? cents : dollars).format(v)
}

function duration(minutes: number | null): string {
  if (minutes === null) return NONE
  if (minutes < 60) return `${Math.round(minutes)}m`
  if (minutes < 1440) return `${decimal.format(minutes / 60)}h`
  return `${decimal.format(minutes / 1440)}d`
}

function shortDate(day: string): string {
  return new Date(`${day}T00:00:00Z`).toLocaleDateString('en', {
    month: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  })
}

/** Adds each row's bar length, as a percentage of the largest amount. */
function scaled<T extends { amount: number }>(rows: T[]) {
  const max = Math.max(0, ...rows.map((r) => r.amount))
  return rows.map((r) => ({ ...r, fill: max ? (r.amount / max) * 100 : 0 }))
}

interface Tile {
  label: string
  value: string
  hint?: string
}

const groups = computed<{ title: string; tiles: Tile[]; note?: string }[]>(() => {
  const s = store.stats
  const k = store.kpis
  const status = store.memory.by_status
  const cost = k.total_cost_usd
  const priced = k.by_model.filter((m) => m.cost_usd !== null)
  const pricedTokens = sum(priced.map((m) => m.input_tokens + m.output_tokens))
  const tokens = s.total_input_tokens + s.total_output_tokens
  const decisions = sum(Object.values(status))
  const accepted = (status.accepted ?? 0) + (status.resolved_with_change ?? 0)
  const rejected = status.rejected ?? 0
  const ofDecisions = (n: number) => (decisions ? `${int.format(n)} of ${plural(decisions, 'tracked finding')}` : undefined)

  return [
    {
      title: 'Activity',
      tiles: [
        { label: 'Reviews', value: int.format(s.total_reviews) },
        { label: 'PRs reviewed', value: int.format(k.total_prs) },
        { label: 'Repositories', value: int.format(k.by_repo.length) },
        { label: 'Reviews (7 days)', value: int.format(sum(k.daily.slice(-7).map((d) => d.reviews))) },
      ],
    },
    {
      title: 'Cost',
      note: k.unpriced_reviews
        ? `${plural(k.unpriced_reviews, 'review')} ran on a model with no known price and ${k.unpriced_reviews === 1 ? 'is' : 'are'} left out of cost figures.`
        : undefined,
      tiles: [
        { label: 'Total cost', value: usd(cost), hint: 'review calls, list price' },
        { label: 'Cost / review', value: usd(div(cost, sum(priced.map((m) => m.reviews)))) },
        { label: 'Cost / PR', value: usd(div(cost, k.total_prs)) },
        { label: 'Cost / finding', value: usd(div(cost, s.total_findings)) },
        { label: 'Cost / 1M tokens', value: usd(div(cost === null ? null : cost * 1e6, pricedTokens)), hint: 'input + output, blended' },
        { label: 'Input tokens', value: compact.format(s.total_input_tokens), hint: int.format(s.total_input_tokens) },
        { label: 'Output tokens', value: compact.format(s.total_output_tokens), hint: int.format(s.total_output_tokens) },
        { label: 'Avg tokens / review', value: show(div(tokens, s.total_reviews), compact) },
      ],
    },
    {
      title: 'Quality',
      tiles: [
        { label: 'Findings', value: int.format(s.total_findings) },
        { label: 'Findings / review', value: show(div(s.total_findings, s.total_reviews), decimal) },
        { label: 'Findings / PR', value: show(div(s.total_findings, k.total_prs), decimal) },
        {
          label: 'Clean reviews',
          value: show(div(k.clean_reviews, s.total_reviews), percent),
          hint: s.total_reviews ? `${int.format(k.clean_reviews)} of ${plural(s.total_reviews, 'review')}` : undefined,
        },
        { label: 'Reviews / PR', value: show(div(s.total_reviews, k.total_prs), decimal) },
        { label: 'Acceptance rate', value: show(div(accepted, decisions), percent), hint: ofDecisions(accepted) },
        { label: 'Rejection rate', value: show(div(rejected, decisions), percent), hint: ofDecisions(rejected) },
        { label: 'Time to first review', value: duration(k.median_minutes_to_first_review), hint: 'median, from PR opened' },
      ],
    },
  ]
})

function counts(values: Record<string, number>, labels: Record<string, string>) {
  return Object.entries(values)
    .sort((a, b) => b[1] - a[1])
    .map(([key, n]) => ({ label: labels[key] ?? key, meta: '', value: int.format(n), amount: n }))
}

// ponytail: every repo and model gets a row; cap the list and fold the tail
// into "Other" once there are more than a screenful.
const breakdowns = computed(() => {
  const { by_repo, by_model, by_axis, by_source } = store.kpis
  return [
    {
      title: 'Cost by repository',
      rows: by_repo.map((r) => ({
        label: r.repo,
        meta: `${plural(r.reviews, 'review')} · ${plural(r.prs, 'PR')}`,
        value: usd(r.cost_usd),
        amount: r.cost_usd ?? 0,
      })),
    },
    {
      title: 'Cost by model',
      rows: by_model.map((m) => ({
        label: m.model,
        meta: `${plural(m.reviews, 'review')} · ${compact.format(m.input_tokens + m.output_tokens)} tokens`,
        value: usd(m.cost_usd),
        amount: m.cost_usd ?? 0,
      })),
    },
    {
      title: 'Findings by repository',
      rows: [...by_repo]
        .sort((a, b) => b.findings - a.findings)
        .map((r) => ({ label: r.repo, meta: '', value: int.format(r.findings), amount: r.findings })),
    },
    { title: 'Findings by axis', rows: counts(by_axis, axisLabels) },
    { title: 'Findings by source', rows: counts(by_source, sourceLabels) },
    { title: 'Rejections by signal', rows: counts(store.memory.by_signal, signalLabels) },
  ].map((card) => ({ ...card, rows: scaled(card.rows) }))
})

const days = computed(() =>
  scaled(store.kpis.daily.map((d) => ({ ...d, label: shortDate(d.date), amount: d.reviews })))
    // a day with a single review must still show next to a busy one
    .map((d) => ({ ...d, fill: d.reviews ? Math.max(d.fill, 4) : 0 })),
)

const hovered = ref<number | null>(null)

function summary(scope: { reviews: number; cost_usd: number | null }[]): string {
  const cost = scope.some((d) => d.cost_usd !== null) ? sum(scope.map((d) => d.cost_usd ?? 0)) : null
  return [plural(sum(scope.map((d) => d.reviews)), 'review'), cost === null ? '' : usd(cost)]
    .filter(Boolean)
    .join(' · ')
}

const readout = computed(() => {
  const day = hovered.value === null ? undefined : days.value[hovered.value]
  return day ? `${day.label} · ${summary([day])}` : summary(days.value)
})
</script>

<template>
  <div class="dashboard">
    <header class="page-header">
      <div>
        <h1>Dashboard</h1>
        <p class="subtitle">PR review activity overview</p>
      </div>
      <button class="refresh-btn" :disabled="refreshing" @click="refresh">
        {{ refreshing ? 'Refreshing…' : 'Refresh' }}
      </button>
    </header>

    <div v-if="loaded" class="content" :class="{ stale: refreshing }" :aria-busy="refreshing">
      <section v-for="(group, i) in groups" :key="group.title">
        <h2>{{ group.title }}</h2>
        <div class="stats-grid">
          <div v-for="tile in group.tiles" :key="tile.label" class="stat-card">
            <span class="stat-label">{{ tile.label }}</span>
            <span class="stat-value">{{ tile.value }}</span>
            <span v-if="tile.hint" class="stat-hint">{{ tile.hint }}</span>
          </div>
        </div>
        <p v-if="group.note" class="note">{{ group.note }}</p>

        <div v-if="i === 0" class="stat-card chart">
          <div class="card-head">
            <span class="stat-label">Reviews per day · last 14 days</span>
            <span class="readout">{{ readout }}</span>
          </div>
          <div
            class="columns"
            role="group"
            aria-label="Reviews per day, last 14 days"
            @pointerleave="hovered = null"
          >
            <div
              v-for="(day, index) in days"
              :key="day.date"
              class="column"
              role="img"
              tabindex="0"
              :aria-label="`${day.label}: ${summary([day])}`"
              @pointerenter="hovered = index"
              @focus="hovered = index"
              @blur="hovered = null"
            >
              <div class="column-bar" :style="{ '--fill': `${day.fill}%` }" />
            </div>
          </div>
          <div class="axis">
            <span>{{ days[0]?.label }}</span>
            <span>{{ days[days.length - 1]?.label }}</span>
          </div>
        </div>
      </section>

      <section>
        <h2>Breakdowns</h2>
        <div class="breakdown-grid">
          <div v-for="card in breakdowns" :key="card.title" class="stat-card">
            <span class="stat-label">{{ card.title }}</span>
            <span v-if="card.rows.length === 0" class="stat-hint">No data yet</span>
            <div v-for="row in card.rows" :key="row.label" class="row">
              <span class="row-label" :title="row.label">
                {{ row.label }}<span v-if="row.meta" class="row-meta">{{ row.meta }}</span>
              </span>
              <span class="row-value">{{ row.value }}</span>
              <div class="bar" :style="{ '--fill': `${row.fill}%` }" />
            </div>
          </div>
        </div>
      </section>

      <section>
        <div class="section-header">
          <h2>Recent Reviews</h2>
          <RouterLink to="/reviews" class="view-all">View all</RouterLink>
        </div>
        <div v-if="store.reviews.length === 0" class="empty">No reviews yet</div>
        <div v-else class="review-list">
          <RouterLink
            v-for="review in store.reviews"
            :key="review.id"
            :to="`/reviews/${review.id}`"
            class="review-row"
          >
            <div class="review-info">
              <span class="review-repo">{{ review.owner }}/{{ review.repo }}</span>
              <span class="review-pr">#{{ review.pr_number }}</span>
              <span class="review-findings">{{ review.total_findings }} findings</span>
            </div>
            <div class="review-meta">
              <span v-if="review.model" class="model-badge">{{ review.model }}</span>
              <span class="review-time" :title="`Last review: ${formatDateTime(review.created_at)}`">
                reviewed {{ timeAgo(review.created_at) }}
              </span>
            </div>
          </RouterLink>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  --ease-out: cubic-bezier(0.23, 1, 0.32, 1);
  --mark: #7c6ef0;
  max-width: 900px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 2rem;
}

.refresh-btn {
  background: #161821;
  color: #e1e4e8;
  border: 1px solid #2a2d3a;
  border-radius: 6px;
  padding: 0.5rem 0.9rem;
  font: inherit;
  font-size: 0.85rem;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s, transform 160ms var(--ease-out);
}

.refresh-btn:active:not(:disabled) {
  transform: scale(0.97);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: default;
}

h1 {
  font-size: 1.5rem;
  font-weight: 600;
}

.subtitle {
  color: #8b8fa3;
  font-size: 0.9rem;
  margin-top: 0.25rem;
}

/* Sections cascade in once, on first load; a refresh only dims them. */
.content {
  transition: opacity 150ms ease;
}

.content.stale {
  opacity: 0.6;
}

.content > section {
  margin-bottom: 2.5rem;
  animation: reveal 300ms var(--ease-out) both;
}

.content > section:nth-child(2) { animation-delay: 50ms; }
.content > section:nth-child(3) { animation-delay: 100ms; }
.content > section:nth-child(4) { animation-delay: 150ms; }
.content > section:nth-child(5) { animation-delay: 200ms; }

@keyframes reveal {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
}

@keyframes fade {
  from {
    opacity: 0;
  }
}

h2 {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
}

.stat-card {
  background: #161821;
  border: 1px solid #2a2d3a;
  border-radius: 8px;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0;
}

.stat-label {
  font-size: 0.8rem;
  color: #8b8fa3;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
}

.stat-hint,
.note {
  font-size: 0.78rem;
  color: #8b8fa3;
}

.note {
  margin-top: 0.75rem;
}

.chart {
  margin-top: 1rem;
  gap: 0.75rem;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 1rem;
}

.readout {
  font-size: 0.85rem;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.columns {
  display: flex;
  height: 96px;
  border-bottom: 1px solid #2a2d3a;
}

/* The whole slot is the hit target, not just the painted bar. */
.column {
  flex: 1;
  display: flex;
  justify-content: center;
  padding: 0 1px;
}

.column:focus-visible {
  outline: 2px solid var(--mark);
  outline-offset: -2px;
  border-radius: 4px;
}

.column-bar {
  width: 100%;
  max-width: 24px;
  background: var(--mark);
  clip-path: inset(calc(100% - var(--fill)) 0 0 0 round 4px 4px 0 0);
  transition: clip-path 250ms var(--ease-out), opacity 150ms ease;
}

.axis {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #8b8fa3;
}

.breakdown-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.3rem 0.75rem;
  align-items: baseline;
  margin-top: 0.6rem;
  font-size: 0.9rem;
}

.row-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.row-meta {
  margin-left: 0.5rem;
  font-size: 0.78rem;
  color: #8b8fa3;
}

.row-value {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.bar {
  grid-column: 1 / -1;
  height: 6px;
  background: var(--mark);
  clip-path: inset(0 calc(100% - var(--fill)) 0 0 round 0 4px 4px 0);
  transition: clip-path 250ms var(--ease-out);
}

/* Bars grow from their baseline the first time they render. */
@starting-style {
  .bar {
    clip-path: inset(0 100% 0 0 round 0 4px 4px 0);
  }

  .column-bar {
    clip-path: inset(100% 0 0 0 round 4px 4px 0 0);
  }
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.view-all {
  font-size: 0.85rem;
  color: #F28C38;
  text-decoration: none;
}

.empty {
  color: #8b8fa3;
  padding: 2rem;
  text-align: center;
  background: #161821;
  border: 1px solid #2a2d3a;
  border-radius: 8px;
}

.review-list {
  display: flex;
  flex-direction: column;
  border: 1px solid #2a2d3a;
  border-radius: 8px;
  overflow: hidden;
}

.review-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.85rem 1rem;
  background: #161821;
  border-bottom: 1px solid #2a2d3a;
  text-decoration: none;
  color: inherit;
  transition: background 0.15s;
}

.review-row:last-child {
  border-bottom: none;
}

.review-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.review-repo {
  color: #F28C38;
  font-size: 0.85rem;
  font-weight: 500;
}

.review-pr {
  color: #8b8fa3;
  font-size: 0.85rem;
}

.review-findings {
  font-size: 0.85rem;
  color: #e1e4e8;
}

.review-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.model-badge {
  font-size: 0.7rem;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  background: rgba(242, 140, 56, 0.15);
  color: #F28C38;
}

.review-time {
  color: #8b8fa3;
  font-size: 0.8rem;
  min-width: 60px;
  text-align: right;
}

/* Touch devices fire :hover on tap, so hover feedback is pointer-only. */
@media (hover: hover) and (pointer: fine) {
  .refresh-btn:hover:not(:disabled) {
    border-color: #7c6ef0;
    color: #7c6ef0;
  }

  .view-all:hover {
    text-decoration: underline;
  }

  .review-row:hover {
    background: #1e2030;
  }

  .columns:hover .column-bar {
    opacity: 0.45;
  }

  .columns .column:hover .column-bar {
    opacity: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .content > section {
    animation-name: fade;
  }

  .bar,
  .column-bar {
    transition: none;
  }

  .refresh-btn:active:not(:disabled) {
    transform: none;
  }
}

@media (max-width: 768px) {
  .dashboard { padding: 0; }
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .review-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  .review-meta {
    width: 100%;
    justify-content: space-between;
  }
}

@media (max-width: 480px) {
  .breakdown-grid {
    grid-template-columns: 1fr;
  }
  .stats-grid {
    grid-template-columns: 1fr;
  }
  .stat-value {
    font-size: 1.4rem;
  }
  .card-head {
    flex-direction: column;
    gap: 0.25rem;
  }
}
</style>
