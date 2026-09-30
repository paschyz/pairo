<script setup lang="ts">
import { watch } from 'vue'
import { useRoute } from 'vue-router'
import { useReviewStore } from '@/stores/reviews'
import { formatDateTime, timeAgo } from '@/utils/time'

const route = useRoute()
const store = useReviewStore()

watch(() => route.params.id, (id) => store.fetchReview(Number(id)), { immediate: true })
</script>

<template>
  <div class="detail-page">
    <RouterLink to="/reviews" class="back-link">&larr; All reviews</RouterLink>

    <div v-if="store.loading" class="empty">Loading...</div>
    <div v-else-if="!store.current" class="empty">Review not found</div>
    <template v-else>
      <header class="page-header">
        <h1>{{ store.current.owner }}/{{ store.current.repo }} #{{ store.current.pr_number }}</h1>
        <div class="header-meta">
          <span v-if="store.current.model" class="model-badge">{{ store.current.model }}</span>
          <span class="meta-item">{{ store.current.input_tokens.toLocaleString() }} in / {{ store.current.output_tokens.toLocaleString() }} out tokens</span>
          <span class="meta-item">{{ store.current.head_sha?.slice(0, 7) }}</span>
        </div>
      </header>

      <section class="timeline">
        <h2>Timeline</h2>
        <ul class="timeline-list">
          <li v-if="store.current.pr_created_at" class="timeline-item">
            <span class="timeline-label">PR opened</span>
            <span class="timeline-time">
              {{ formatDateTime(store.current.pr_created_at) }} ({{ timeAgo(store.current.pr_created_at) }})
            </span>
          </li>
          <li
            v-for="h in [...store.current.history].reverse()"
            :key="h.id"
            class="timeline-item"
            :class="{ current: h.id === store.current.id }"
          >
            <RouterLink :to="`/reviews/${h.id}`" class="timeline-label">
              Review {{ h.head_sha?.slice(0, 7) }} · {{ h.total_findings }} findings
            </RouterLink>
            <span class="timeline-time">{{ formatDateTime(h.created_at) }} ({{ timeAgo(h.created_at) }})</span>
          </li>
        </ul>
      </section>

      <section class="findings">
        <h2>Findings ({{ store.current.findings.length }})</h2>
        <div v-if="store.current.findings.length === 0" class="empty">No findings</div>
        <div v-else class="finding-list">
          <div v-for="(f, i) in store.current.findings" :key="i" class="finding-card">
            <div class="finding-header">
              <span class="finding-axis">{{ f.axis }}</span>
              <span v-if="f.file" class="finding-file">{{ f.file }}<span v-if="f.line">:{{ f.line }}</span></span>
            </div>
            <p class="finding-issue">{{ f.issue }}</p>
            <p v-if="f.suggestion" class="finding-suggestion">{{ f.suggestion }}</p>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.detail-page { max-width: 900px; }

.back-link {
  display: inline-block; margin-bottom: 1.5rem;
  color: #F28C38; text-decoration: none; font-size: 0.85rem;
}
.back-link:hover { text-decoration: underline; }

.page-header { margin-bottom: 2rem; }
h1 { font-size: 1.3rem; font-weight: 600; }

.header-meta {
  display: flex; align-items: center; gap: 1rem;
  margin-top: 0.5rem; font-size: 0.8rem; color: #8b8fa3;
}
.model-badge {
  font-size: 0.7rem; padding: 0.15rem 0.4rem; border-radius: 4px;
  background: rgba(242, 140, 56, 0.15); color: #F28C38;
}

.timeline { margin-bottom: 2rem; }
.timeline-list {
  list-style: none; background: #161821; border: 1px solid #2a2d3a; border-radius: 8px;
}
.timeline-item {
  display: flex; justify-content: space-between; gap: 1rem; flex-wrap: wrap;
  padding: 0.6rem 1rem; font-size: 0.85rem;
}
.timeline-item + .timeline-item { border-top: 1px solid #2a2d3a; }
.timeline-item.current { background: #1e2030; }
.timeline-item.current .timeline-label { font-weight: 600; }
.timeline-label { color: #e1e4e8; text-decoration: none; }
a.timeline-label:hover { color: #F28C38; }
.timeline-time { color: #8b8fa3; }

h2 { font-size: 1.1rem; font-weight: 600; margin-bottom: 1rem; }

.empty {
  color: #8b8fa3; padding: 2rem; text-align: center;
  background: #161821; border: 1px solid #2a2d3a; border-radius: 8px;
}

.finding-list { display: flex; flex-direction: column; gap: 0.75rem; }

.finding-card {
  background: #161821; border: 1px solid #2a2d3a; border-radius: 8px;
  padding: 1rem;
}

.finding-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 0.5rem;
}
.finding-axis {
  font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.04em;
  color: #F28C38; font-weight: 600;
}
.finding-file { font-size: 0.8rem; color: #8b8fa3; font-family: monospace; }

.finding-issue { font-size: 0.9rem; line-height: 1.5; }

.finding-suggestion {
  margin-top: 0.5rem; font-size: 0.85rem; color: #8b8fa3;
  padding-top: 0.5rem; border-top: 1px solid #2a2d3a;
}

@media (max-width: 768px) {
  .finding-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }
  .finding-file {
    word-break: break-all;
  }
}
</style>
