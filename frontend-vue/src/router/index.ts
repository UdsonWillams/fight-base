import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
  },
  {
    path: '/fighters',
    name: 'fighters',
    component: () => import('../views/FightersView.vue'),
  },
  {
    path: '/fighters/:id',
    name: 'fighter-detail',
    component: () => import('../views/FighterDetailsView.vue'),
  },
  {
    path: '/simulate',
    name: 'simulate',
    component: () => import('../views/SimulateView.vue'),
  },
  {
    path: '/events',
    name: 'events',
    component: () => import('../views/EventsView.vue'),
  },
  {
    path: '/events/create',
    name: 'event-create',
    component: () => import('../views/CreateEventView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/events/:id',
    name: 'event-detail',
    component: () => import('../views/EventDetailsView.vue'),
  },
  {
    path: '/events/:id/edit',
    name: 'event-edit',
    component: () => import('../views/EditEventView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/rankings',
    name: 'rankings',
    component: () => import('../views/RankingsView.vue'),
  },
  {
    path: '/leagues',
    name: 'leagues',
    component: () => import('../views/LeaguesView.vue'),
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/RegisterView.vue'),
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router
