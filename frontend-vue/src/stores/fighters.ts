import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/services/api'
import type { Fighter, FighterCreate, FighterStats } from '@/types'

export const useFighterStore = defineStore('fighters', () => {
  const fighters = ref<Fighter[]>([])
  const currentFighter = ref<Fighter | null>(null)
  const stats = ref<FighterStats | null>(null)
  const total = ref(0)
  const page = ref(1)
  const pages = ref(1)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchFighters(params?: Record<string, string | number | boolean>) {
    loading.value = true
    error.value = null
    try {
      const res = await api.getFighters(params as Record<string, string | number>)
      fighters.value = res.fighters || []
      total.value = res.total || 0
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro ao buscar lutadores'
      error.value = msg
    } finally {
      loading.value = false
    }
  }

  async function fetchFighter(id: string) {
    loading.value = true
    error.value = null
    try {
      currentFighter.value = await api.getFighter(id)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro ao buscar lutador'
      error.value = msg
      currentFighter.value = null
    } finally {
      loading.value = false
    }
  }

  async function createFighter(data: FighterCreate) {
    loading.value = true
    error.value = null
    try {
      const fighter = await api.createFighter(data)
      fighters.value.unshift(fighter)
      return fighter
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro ao criar lutador'
      error.value = msg
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateFighter(id: string, data: Partial<FighterCreate>) {
    loading.value = true
    error.value = null
    try {
      const updated = await api.updateFighter(id, data)
      const idx = fighters.value.findIndex((f) => f.id === id)
      if (idx !== -1) fighters.value[idx] = updated
      if (currentFighter.value?.id === id) currentFighter.value = updated
      return updated
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro ao atualizar lutador'
      error.value = msg
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteFighter(id: string) {
    loading.value = true
    error.value = null
    try {
      await api.deleteFighter(id)
      fighters.value = fighters.value.filter((f) => f.id !== id)
      if (currentFighter.value?.id === id) currentFighter.value = null
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro ao deletar lutador'
      error.value = msg
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchStats() {
    try {
      stats.value = await api.getFighterStats()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro ao buscar estatísticas'
      error.value = msg
    }
  }

  return {
    fighters,
    currentFighter,
    stats,
    total,
    page,
    pages,
    loading,
    error,
    fetchFighters,
    fetchFighter,
    createFighter,
    updateFighter,
    deleteFighter,
    fetchStats,
  }
})
