<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useReviewStore } from '@/stores/reviews'

const store = useReviewStore()
const offset = ref(0)
const limit = 20

onMounted(() => store.fetchReviews(offset.value, limit))

async function loadMore() {
  offset.value += limit
  await store.fetchReviews(offset.value, limit)
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
  <div class="reviews-page">
    <header class="page-header">
      <h1>Reviews</h1>
      <p class="subtitle">All PR reviews</p>
    </header>

    <div v-if="store.loading && store.reviews.length === 0" class="empty">Loading...</div>
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

    <button
      v-if="store.reviews.length >= offset + limit"
      class="load-more"
      :disabled="store.loading"
      @click="loadMore"
    >
      {{ store.loading ? 'Loading...' : 'Load more' }}
    </button>
  </div>
</template>

<style scoped>
.reviews-page { max-width: 900px; }
.page-header { margin-bottom: 2rem; }
h1 { font-size: 1.5rem; font-weight: 600; }
.subtitle { color: #8b8fa3; font-size: 0.9rem; margin-top: 0.25rem; }

.empty {
  color: #8b8fa3; padding: 2rem; text-align: center;
  background: #161821; border: 1px solid #2a2d3a; border-radius: 8px;
}

.review-list {
  display: flex; flex-direction: column;
  border: 1px solid #2a2d3a; border-radius: 8px; overflow: hidden;
}

.review-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.85rem 1rem; background: #161821;
  border-bottom: 1px solid #2a2d3a;
  text-decoration: none; color: inherit; transition: background 0.15s;
}
.review-row:last-child { border-bottom: none; }
.review-row:hover { background: #1e2030; }

.review-info { display: flex; align-items: center; gap: 0.5rem; }
.review-repo { color: #7c6ef0; font-size: 0.85rem; font-weight: 500; }
.review-pr { color: #8b8fa3; font-size: 0.85rem; }
.review-findings { font-size: 0.85rem; color: #e1e4e8; }

.review-meta { display: flex; align-items: center; gap: 0.75rem; }
.model-badge {
  font-size: 0.7rem; padding: 0.15rem 0.4rem; border-radius: 4px;
  background: rgba(124, 110, 240, 0.15); color: #7c6ef0;
}
.review-time { color: #8b8fa3; font-size: 0.8rem; min-width: 60px; text-align: right; }

.load-more {
  display: block; margin: 1.5rem auto 0; padding: 0.6rem 1.5rem;
  background: #1e2030; color: #e1e4e8; border: 1px solid #2a2d3a;
  border-radius: 6px; cursor: pointer; font-size: 0.85rem;
}
.load-more:hover { background: #282a3a; }
.load-more:disabled { opacity: 0.5; cursor: default; }
</style>
