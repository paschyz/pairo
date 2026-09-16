import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface ReviewSummary {
  id: number
  delivery_id: string
  owner: string
  repo: string
  pr_number: number
  head_sha: string
  model: string | null
  input_tokens: number
  output_tokens: number
  total_findings: number
  created_at: string | null
}

export interface Finding {
  axis: string
  file: string
  line: number | null
  issue: string
  suggestion: string
  source: string
}

export interface ReviewDetail extends Omit<ReviewSummary, 'total_findings'> {
  findings: Finding[]
}

export interface Stats {
  total_reviews: number
  total_findings: number
  total_input_tokens: number
  total_output_tokens: number
}

export const useReviewStore = defineStore('reviews', () => {
  const reviews = ref<ReviewSummary[]>([])
  const current = ref<ReviewDetail | null>(null)
  const stats = ref<Stats>({ total_reviews: 0, total_findings: 0, total_input_tokens: 0, total_output_tokens: 0 })
  const loading = ref(false)

  async function fetchReviews(offset = 0, limit = 20) {
    loading.value = true
    try {
      const res = await fetch(`/api/reviews?offset=${offset}&limit=${limit}`)
      reviews.value = await res.json()
    } finally {
      loading.value = false
    }
  }

  async function fetchReview(id: number) {
    loading.value = true
    try {
      const res = await fetch(`/api/reviews/${id}`)
      if (res.ok) {
        current.value = await res.json()
      }
    } finally {
      loading.value = false
    }
  }

  async function fetchStats() {
    const res = await fetch('/api/stats')
    stats.value = await res.json()
  }

  return { reviews, current, stats, loading, fetchReviews, fetchReview, fetchStats }
})
