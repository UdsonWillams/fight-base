<template>
  <nav class="glass-navbar">
    <div class="navbar-inner">
      <RouterLink to="/#/" class="logo" @click="closeMenu">
        <span class="logo-icon">&#x1F94A;</span>
        <span class="logo-text">FightBase</span>
      </RouterLink>

      <div class="nav-links" :class="{ 'nav-open': menuOpen }">
        <RouterLink to="/" class="nav-link" active-class="nav-link--active" @click="closeMenu">
          {{ t('nav.home') }}
        </RouterLink>
        <RouterLink to="/fighters" class="nav-link" active-class="nav-link--active" @click="closeMenu">
          {{ t('nav.fighters') }}
        </RouterLink>
        <RouterLink to="/simulate" class="nav-link" active-class="nav-link--active" @click="closeMenu">
          {{ t('nav.simulate') }}
        </RouterLink>
        <RouterLink to="/events" class="nav-link" active-class="nav-link--active" @click="closeMenu">
          {{ t('nav.events') }}
        </RouterLink>
        <RouterLink to="/rankings" class="nav-link" active-class="nav-link--active" @click="closeMenu">
          {{ t('nav.rankings') }}
        </RouterLink>
        <RouterLink to="/leagues" class="nav-link" active-class="nav-link--active" @click="closeMenu">
          {{ t('nav.leagues') }}
        </RouterLink>
      </div>

      <div class="nav-actions">
        <div class="lang-switcher">
          <button class="lang-flag" :class="{ active: locale === 'pt-BR' }" @click="setLocale('pt-BR')" title="Portugues">🇧🇷</button>
          <button class="lang-flag" :class="{ active: locale === 'en-US' }" @click="setLocale('en-US')" title="English">🇺🇸</button>
        </div>
        <template v-if="auth.isLoggedIn">
          <span class="username">{{ auth.user?.name }}</span>
          <button class="btn btn-ghost" @click="handleLogout">
            {{ t('nav.logout') }}
          </button>
        </template>
        <template v-else>
          <button class="btn btn-ghost" @click="router.push('/login')">
            {{ t('nav.login') }}
          </button>
          <button class="btn btn-primary" @click="router.push('/register')">
            {{ t('nav.register') }}
          </button>
        </template>
      </div>

      <button class="hamburger" @click="menuOpen = !menuOpen" :aria-label="menuOpen ? 'Fechar menu' : 'Abrir menu'">
        <span></span>
        <span></span>
        <span></span>
      </button>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'

const { t, locale } = useI18n()
const router = useRouter()
const auth = useAuthStore()
const menuOpen = ref(false)

function setLocale(loc: string) {
  locale.value = loc
  localStorage.setItem('locale', loc)
}

function handleLogout() {
  auth.logout()
  menuOpen.value = false
  router.push('/')
}

function closeMenu() {
  menuOpen.value = false
}
</script>

<style scoped>
.navbar-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 16px;
  height: 100%;
}

.navbar-inner > * {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  color: var(--text-primary);
  font-weight: 700;
  font-size: 1.25rem;
  flex-shrink: 0;
}

.logo-icon {
  font-size: 1.4rem;
}

.logo-text {
  background: linear-gradient(135deg, var(--accent-light), var(--primary-light));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 4px;
}

.nav-link {
  color: var(--text-secondary);
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 25px;
  font-size: 0.875rem;
  font-weight: 500;
  line-height: 1.4;
  transition: all var(--transition);
  white-space: nowrap;
}

.nav-link:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.05);
}

.nav-link--active {
  color: var(--text-primary);
  background: rgba(124, 58, 237, 0.2);
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.lang-switcher {
  display: flex;
  gap: 4px;
  margin-right: 10px;
}

.lang-flag {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 6px;
  padding: 2px 6px;
  font-size: 1.1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  line-height: 1;
  opacity: 0.45;
}

.lang-flag:hover {
  opacity: 0.8;
  background: rgba(255,255,255,0.06);
}

.lang-flag.active {
  opacity: 1;
  background: rgba(255,255,255,0.1);
  border-color: rgba(255,255,255,0.2);
  box-shadow: 0 0 8px rgba(255,255,255,0.08);
}

.username {
  color: var(--text-primary);
  font-size: 0.875rem;
  font-weight: 500;
  margin-right: 4px;
}

.btn {
  padding: 8px 18px;
  border-radius: 25px;
  font-size: 0.8125rem;
  font-weight: 600;
  line-height: 1.4;
  border: none;
  cursor: pointer;
  transition: all var(--transition);
  white-space: nowrap;
}

.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--glass-border);
}

.btn-ghost:hover {
  color: var(--text-primary);
  border-color: var(--glass-border-hover);
  background: rgba(255, 255, 255, 0.05);
}

.btn-primary {
  background: linear-gradient(135deg, var(--accent), var(--accent-dark));
  color: #fff;
}

.btn-primary:hover {
  filter: brightness(1.15);
  transform: translateY(-1px);
}

.hamburger {
  display: none;
  flex-direction: column;
  gap: 5px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
}

.hamburger span {
  display: block;
  width: 22px;
  height: 2px;
  background: var(--text-primary);
  border-radius: 2px;
  transition: all var(--transition);
}

@media (max-width: 768px) {
  .nav-links {
    display: none;
    position: absolute;
    top: calc(100% + 12px);
    left: 0;
    right: 0;
    flex-direction: column;
    background: var(--glass-bg);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 1px solid var(--glass-border);
    border-radius: 20px;
    padding: 16px;
    gap: 4px;
    box-shadow: var(--glass-shadow);
  }

  .nav-links.nav-open {
    display: flex;
  }

  .nav-link {
    width: 100%;
    text-align: center;
    padding: 12px;
  }

  .hamburger {
    display: flex;
  }

  .nav-actions .username {
    display: none;
  }
}
</style>
