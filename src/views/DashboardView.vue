<script setup lang="ts">
const stats = [
  { label: 'Reviews Today', value: '12', trend: '+3' },
  { label: 'Open PRs', value: '7', trend: '-2' },
  { label: 'Avg Response', value: '4m', trend: '-12s' },
  { label: 'Repos Connected', value: '3', trend: '' },
]

const recentReviews = [
  { repo: 'acme/api', pr: '#342', title: 'Add rate limiting middleware', status: 'completed', time: '2m ago' },
  { repo: 'acme/web', pr: '#189', title: 'Fix auth redirect loop', status: 'completed', time: '8m ago' },
  { repo: 'acme/api', pr: '#341', title: 'Migrate user schema v3', status: 'in-progress', time: '12m ago' },
  { repo: 'acme/shared', pr: '#57', title: 'Update eslint config', status: 'queued', time: '15m ago' },
]
</script>

<template>
  <div class="dashboard">
    <header class="page-header">
      <h1>Dashboard</h1>
      <p class="subtitle">PR review activity overview</p>
    </header>

    <div class="stats-grid">
      <div v-for="stat in stats" :key="stat.label" class="stat-card">
        <span class="stat-label">{{ stat.label }}</span>
        <span class="stat-value">{{ stat.value }}</span>
        <span v-if="stat.trend" class="stat-trend">{{ stat.trend }}</span>
      </div>
    </div>

    <section class="recent">
      <h2>Recent Reviews</h2>
      <div class="review-list">
        <div v-for="review in recentReviews" :key="review.pr" class="review-row">
          <div class="review-info">
            <span class="review-repo">{{ review.repo }}</span>
            <span class="review-pr">{{ review.pr }}</span>
            <span class="review-title">{{ review.title }}</span>
          </div>
          <div class="review-meta">
            <span :class="['status-badge', review.status]">{{ review.status }}</span>
            <span class="review-time">{{ review.time }}</span>
          </div>
        </div>
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

.stat-trend {
  font-size: 0.8rem;
  color: #4ade80;
}

h2 {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 1rem;
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
  color: #7c6ef0;
  font-size: 0.85rem;
  font-weight: 500;
}

.review-pr {
  color: #8b8fa3;
  font-size: 0.85rem;
}

.review-title {
  font-size: 0.9rem;
}

.review-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.status-badge {
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  text-transform: capitalize;
}

.status-badge.completed {
  background: rgba(74, 222, 128, 0.15);
  color: #4ade80;
}

.status-badge.in-progress {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
}

.status-badge.queued {
  background: rgba(139, 143, 163, 0.15);
  color: #8b8fa3;
}

.review-time {
  color: #8b8fa3;
  font-size: 0.8rem;
  min-width: 60px;
  text-align: right;
}
</style>
