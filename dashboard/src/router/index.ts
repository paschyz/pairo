import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import DashboardView from '@/views/DashboardView.vue'
import ReviewsView from '@/views/ReviewsView.vue'
import ReviewDetailView from '@/views/ReviewDetailView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/dashboard', name: 'dashboard', component: DashboardView, meta: { layout: 'dashboard' } },
    { path: '/reviews', name: 'reviews', component: ReviewsView, meta: { layout: 'dashboard' } },
    { path: '/reviews/:id', name: 'review-detail', component: ReviewDetailView, meta: { layout: 'dashboard' } },
  ],
})

export default router
