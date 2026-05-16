import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/services/api'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('idToken'))
  const loading = ref(false)

  // Garante que o token existente no localStorage seja setado na API ao inicializar
  if (token.value) {
    api.setToken(token.value)
  }

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const username = computed(() => user.value?.name ?? '')

  async function checkAuth(): Promise<boolean> {
    if (!token.value) return false
    api.setToken(token.value)
    try {
      user.value = await api.getCurrentUser()
      return !!user.value
    } catch {
      logout()
      return false
    }
  }

  async function login(email: string, password: string) {
    loading.value = true
    try {
      const response = await api.login(email, password)
      token.value = response.access_token
      api.setToken(token.value)
      localStorage.setItem('idToken', token.value)
      user.value = await api.getCurrentUser()
    } finally {
      loading.value = false
    }
  }

  async function register(data: { email: string; password: string; username: string; name: string; avatar?: string; birth_date?: string }) {
    loading.value = true
    try {
      await api.register(data)
    } finally {
      loading.value = false
    }
  }

  function logout() {
    token.value = null
    user.value = null
    api.setToken(null)
    localStorage.removeItem('idToken')
  }

  return {
    user,
    token,
    loading,
    isLoggedIn,
    isAdmin,
    username,
    checkAuth,
    login,
    register,
    logout,
  }
})
