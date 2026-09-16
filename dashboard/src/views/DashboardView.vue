<script setup lang="ts">
import { onMounted } from 'vue'
import { useReviewStore } from '@/stores/reviews'

const store = useReviewStore()

onMounted(async () => {
  await Promise.all([store.fetchStats(), store.fetchReviews(0, 5)])
})

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
      <h1>Dashboard</h1>
      <p class="subtitle">PR review activity overview</p>
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
  margin-bottom: 2rem;
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
  color: #7c6ef0;
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
  color: #7c6ef0;
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
  background: rgba(124, 110, 240, 0.15);
  color: #7c6ef0;
}

.review-time {
  color: #8b8fa3;
  font-size: 0.8rem;
  min-width: 60px;
  text-align: right;
}
</style>
