<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useReviewStore } from '@/stores/reviews'

const store = useReviewStore()

const refreshing = ref(false)

async function refresh() {
  refreshing.value = true
  try {
    await Promise.all([store.fetchStats(), store.fetchMemoryStats(), store.fetchReviews(0, 5)])
  } finally {
    refreshing.value = false
  }
}

onMounted(refresh)

const signalLabels: Record<string, string> = {
  command: '@pairo ignore',
  reaction: '👎 reaction',
  resolved_unchanged: 'Resolved thread',
  reply_llm: 'Reply',
}

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return ''
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}
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

    <div class="stats-grid">
      <div class="stat-card">
        <span class="stat-label">Total Reviews</span>
        <span class="stat-value">{{ store.stats.total_reviews }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Total Findings</span>
        <span class="stat-value">{{ store.stats.total_findings }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Input Tokens</span>
        <span class="stat-value">{{ store.stats.total_input_tokens.toLocaleString() }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Output Tokens</span>
        <span class="stat-value">{{ store.stats.total_output_tokens.toLocaleString() }}</span>
      </div>
    </div>

    <section class="rejections">
      <div class="section-header">
        <h2>Rejections</h2>
        <span class="review-pr">{{ store.memory.total_rejected }} total</span>
      </div>
      <div v-if="store.memory.total_rejected === 0" class="empty">No rejections yet</div>
      <div v-else class="rejection-grid">
        <div class="stat-card">
          <span class="stat-label">By signal</span>
          <div v-for="(n, k) in store.memory.by_signal" :key="k" class="rejection-row">
            <span>{{ signalLabels[k] ?? k }}</span><span>{{ n }}</span>
          </div>
        </div>
        <div class="stat-card">
          <span class="stat-label">By category</span>
          <div v-for="(n, k) in store.memory.by_category" :key="k" class="rejection-row">
            <span>{{ k || 'uncategorized' }}</span><span>{{ n }}</span>
          </div>
        </div>
      </div>
    </section>

    <section class="recent">
      <div class="section-header">
        <h2>Recent Reviews</h2>
        <RouterLink to="/reviews" class="view-all">View all</RouterLink>
      </div>
      <div v-if="store.loading" class="empty">Loading...</div>
      <div v-else-if="store.reviews.length === 0" class="empty">No reviews yet</div>
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
            <span class="review-time">{{ timeAgo(review.created_at) }}</span>
          </div>
        </RouterLink>
      </div>
    </section>
  </div>
</template>

<style scoped>
.dashboard {
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
  transition: border-color 0.15s, color 0.15s;
}

.refresh-btn:hover:not(:disabled) {
  border-color: #7c6ef0;
  color: #7c6ef0;
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 2.5rem;
}

.stat-card {
  background: #161821;
  border: 1px solid #2a2d3a;
  border-radius: 8px;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.stat-label {
  font-size: 0.8rem;
  color: #8b8fa3;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
}

.rejections {
  margin-bottom: 2.5rem;
}

.rejection-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.rejection-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

h2 {
  font-size: 1.1rem;
  font-weight: 600;
}

.view-all {
  font-size: 0.85rem;
  color: #F28C38;
  text-decoration: none;
}

.view-all:hover {
  text-decoration: underline;
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

.review-row:hover {
  background: #1e2030;
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
  .rejection-grid {
    grid-template-columns: 1fr;
  }
  .stats-grid {
    grid-template-columns: 1fr;
  }
  .stat-value {
    font-size: 1.4rem;
  }
}
</style>
