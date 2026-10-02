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
  pr_created_at: string | null
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

export interface ReviewHistoryItem {
  id: number
  head_sha: string
  total_findings: number
  created_at: string | null
}

export interface ReviewDetail extends Omit<ReviewSummary, 'total_findings'> {
  history: ReviewHistoryItem[]
  findings: Finding[]
}

export interface Stats {
  total_reviews: number
  total_findings: number
  total_input_tokens: number
  total_output_tokens: number
}

export interface MemoryStats {
  total_rejected: number
  by_signal: Record<string, number>
  by_status: Record<string, number>
}

export interface Usage {
  reviews: number
  input_tokens: number
  output_tokens: number
  cost_usd: number | null
}

export interface Kpis {
  total_cost_usd: number | null
  unpriced_reviews: number
  total_prs: number
  clean_reviews: number
  median_minutes_to_first_review: number | null
  by_repo: (Usage & { repo: string; prs: number; findings: number })[]
  by_model: (Usage & { model: string })[]
  by_axis: Record<string, number>
  by_source: Record<string, number>
  daily: (Usage & { date: string })[]
}

export const useReviewStore = defineStore('reviews', () => {
  const reviews = ref<ReviewSummary[]>([])
  const current = ref<ReviewDetail | null>(null)
  const stats = ref<Stats>({ total_reviews: 0, total_findings: 0, total_input_tokens: 0, total_output_tokens: 0 })
  const memory = ref<MemoryStats>({ total_rejected: 0, by_signal: {}, by_status: {} })
  const kpis = ref<Kpis>({
    total_cost_usd: null,
    unpriced_reviews: 0,
    total_prs: 0,
    clean_reviews: 0,
    median_minutes_to_first_review: null,
    by_repo: [],
    by_model: [],
    by_axis: {},
    by_source: {},
    daily: [],
  })
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

  async function fetchMemoryStats() {
    const res = await fetch('/api/stats/memory')
    memory.value = await res.json()
  }

  async function fetchKpis() {
    const res = await fetch('/api/stats/kpis')
    kpis.value = await res.json()
  }

  return { reviews, current, stats, memory, kpis, loading, fetchReviews, fetchReview, fetchStats, fetchMemoryStats, fetchKpis }
})
