# 🎨 FightBase - Guia do Frontend (Vue 3)

> Documentação completa do frontend Vue 3 + TypeScript + PrimeVue + Tailwind CSS

## 📁 Estrutura de Arquivos

```
frontend-vue/
├── index.html                 # SPA entry (Inter + Outfit fonts, dark theme)
├── package.json               # Dependências e scripts
├── vite.config.ts             # Vite + Vue + Tailwind + proxy config
├── tsconfig.json              # TypeScript config
├── env.d.ts                   # Vue/Vite type declarations
├── dist/                      # Build de produção
├── public/
└── src/
    ├── App.vue                # Componente raiz
    ├── main.ts                # Entry point (Pinia, PrimeVue, i18n, Router)
    ├── assets/
    │   └── css/
    │       └── theme.css      # PrimeVue + custom CSS theme
    ├── components/
    │   ├── auth/              # Login/Register UI
    │   ├── events/            # EventCard, EventForm
    │   ├── fighters/          # FighterCard, FighterList
    │   ├── layout/            # Navbar, Footer, Layout
    │   ├── predictions/       # Prediction UI
    │   ├── simulation/        # Fight simulation UI
    │   └── ui/                # Shared UI components
    ├── composables/           # Vue composables
    ├── locales/
    │   ├── pt-BR.json         # Portuguese translations
    │   └── en-US.json         # English translations
    ├── router/
    │   └── index.ts           # Vue Router (hash mode, auth guards)
    ├── services/
    │   └── api.ts             # Axios API client
    ├── stores/                # Pinia state stores
    │   ├── auth.ts            # Authentication
    │   ├── events.ts          # Events
    │   ├── fighters.ts        # Fighters
    │   ├── league.ts          # Leagues
    │   ├── predictions.ts     # Predictions
    │   ├── simulation.ts      # Simulation
    │   └── toast.ts           # Toast notifications
    ├── types/
    │   └── index.ts           # TypeScript type definitions
    ├── utils/                 # Utility functions
    └── views/                 # Page views (14 views)
        ├── AdminView.vue
        ├── CreateEventView.vue
        ├── EditEventView.vue
        ├── EventDetailsView.vue
        ├── EventsView.vue
        ├── FighterDetailsView.vue
        ├── FightersView.vue
        ├── HomeView.vue
        ├── LeagueDetailView.vue
        ├── LeaguesView.vue
        ├── LoginView.vue
        ├── RankingsView.vue
        ├── RegisterView.vue
        └── SimulateView.vue
```

## 🚀 Desenvolvimento

### Scripts

```bash
# Instalar dependências
cd frontend-vue
npm install

# Dev server com hot reload (http://localhost:5173)
npm run dev

# Build de produção
npm run build

# Preview do build
npm run preview
```

### Configuração do Vite

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: { '@': resolve(__dirname, 'src') },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8080', changeOrigin: true },
      '/swagger': { target: 'http://localhost:8080', changeOrigin: true },
      '/docs': { target: 'http://localhost:8080', changeOrigin: true },
    },
  },
})
```

## 🎯 Principais Recursos

### Stack Tecnológica

| Tecnologia | Versão | Propósito |
|-----------|--------|-----------|
| Vue 3 | 3.5+ | Framework SPA |
| TypeScript | 5.8+ | Type safety |
| Vite | 6.3+ | Bundler e dev server |
| PrimeVue | 4.3+ | UI components |
| Tailwind CSS | 4.1+ | Utility-first CSS |
| Pinia | 3.0+ | State management |
| Vue Router | 4.5+ | Navegação |
| Vue i18n | 11.1+ | Internacionalização |
| Axios | — | HTTP client |
| canvas-confetti | — | Efeitos visuais |

### 🌐 Internacionalização (i18n)

Suporte completo para português e inglês:

```typescript
// src/main.ts
import { createI18n } from 'vue-i18n'
import ptBR from './locales/pt-BR.json'
import enUS from './locales/en-US.json'

const i18n = createI18n({
  legacy: false,
  locale: 'pt-BR',
  fallbackLocale: 'en-US',
  messages: { 'pt-BR': ptBR, 'en-US': enUS },
})
```

### 🛡️ Router com Auth Guards

```typescript
// src/router/index.ts
const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/fighters', name: 'fighters', component: FightersView },
  { path: '/fighters/:id', name: 'fighter-details', component: FighterDetailsView },
  { path: '/events', name: 'events', component: EventsView },
  { path: '/events/:id', name: 'event-details', component: EventDetailsView },
  { path: '/simulate', name: 'simulate', component: SimulateView, meta: { requiresAuth: true } },
  { path: '/rankings', name: 'rankings', component: RankingsView },
  { path: '/leagues', name: 'leagues', component: LeaguesView },
  { path: '/leagues/:id', name: 'league-detail', component: LeagueDetailView },
  { path: '/login', name: 'login', component: LoginView },
  { path: '/register', name: 'register', component: RegisterView },
  { path: '/admin', name: 'admin', component: AdminView, meta: { requiresAdmin: true } },
]

// Guards
router.beforeEach((to, _, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isAuthenticated) next('/login')
  else if (to.meta.requiresAdmin && !authStore.isAdmin) next('/')
  else next()
})
```

### 🗃️ Pinia Stores

```typescript
// Exemplo: stores/auth.ts
import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('access_token'),
    user: JSON.parse(localStorage.getItem('user') || 'null'),
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => state.user?.role === 'admin',
  },
  actions: {
    async login(email: string, password: string) { /* ... */ },
    logout() { /* ... */ },
  },
})
```

### 🌐 API Client

```typescript
// src/services/api.ts
import axios from 'axios'

const api = axios.create({ baseURL: '/api/v1' })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
```

## 🎨 Tema e Estilização

### Tailwind CSS + PrimeVue

A combinação permite usar classes utilitárias do Tailwind com componentes ricos do PrimeVue:

```vue
<template>
  <div class="min-h-screen bg-gray-950 text-white">
    <Button label="Simular Luta" severity="danger" @click="simulate" />
    <DataTable :value="fighters" class="mt-4" />
  </div>
</template>
```

### PrimeVue Theme

Configurado no `main.ts` via `@primeuix/themes` com tema escuro customizado e estilos complementares em `assets/css/theme.css`.

## 📱 Views Principais

| View | Rota | Descrição |
|------|------|-----------|
| HomeView | `/` | Landing page com busca de lutadores |
| FightersView | `/fighters` | Lista de lutadores com filtros |
| FighterDetailsView | `/fighters/:id` | Perfil completo com stats |
| EventsView | `/events` | Lista de eventos |
| EventDetailsView | `/events/:id` | Card do evento com lutas |
| SimulateView | `/simulate` | Interface de simulação |
| RankingsView | `/rankings` | Rankings por categoria/org |
| LeaguesView | `/leagues` | Lista de ligas |
| LoginView | `/login` | Login (email + Google OAuth) |
| AdminView | `/admin` | Painel administrativo |

## ⚡ Performance

- **Vite HMR**: Hot module replacement instantâneo
- **Tree shaking**: Bundle reduzido via ES modules
- **Code splitting**: Lazy loading de views via Vue Router
- **Proxy integrado**: Dev server encaminha `/api/*` direto pro backend

## 📝 TODO: Melhorias Futuras

- [ ] PWA support com Service Worker
- [ ] Gráficos radar/pizza com Chart.js
- [ ] Upload de fotos de lutadores
- [ ] Testes unitários com Vitest
- [ ] Testes E2E com Playwright

---

**Stack:** Vue 3 + TypeScript + Vite + PrimeVue + Tailwind CSS + Pinia + Vue Router + i18n
