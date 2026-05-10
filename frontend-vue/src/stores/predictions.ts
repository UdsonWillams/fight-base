import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/services/api'
import type { Prediction, Achievement, League, LeaderboardEntry } from '@/types'

export const usePredictionStore = defineStore('predictions', () => {
  const predictions = ref<Prediction[]>([])
  const leaderboard = ref<LeaderboardEntry[]>([])
  const achievements = ref<Achievement[]>([])
  const leagues = ref<League[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchPredictions(eventId: string) {
    loading.value = true
    error.value = null
    try {
      predictions.value = await api.getMyPredictions(eventId)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro ao buscar predições'
      error.value = msg
    } finally {
      loading.value = false
    }
  }

  async function fetchLeaderboard(eventId: string, limit: number = 10) {
    loading.value = true
    error.value = null
    try {
      leaderboard.value = await api.getEventLeaderboard(eventId, limit)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro ao buscar leaderboard'
      error.value = msg
    } finally {
      loading.value = false
    }
  }

  async function fetchAchievements() {
    loading.value = true
    error.value = null
    try {
      achievements.value = await api.getAchievements()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro ao buscar conquistas'
      error.value = msg
    } finally {
      loading.value = false
    }
  }

  async function fetchLeagues() {
    loading.value = true
    error.value = null
    try {
      leagues.value = await api.getMyLeagues()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro ao buscar ligas'
      error.value = msg
    } finally {
      loading.value = false
    }
  }

  async function createLeague(data: { name: string; description?: string }) {
    loading.value = true
    error.value = null
    try {
      const league = await api.createLeague(data)
      leagues.value.push(league)
      return league
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro ao criar liga'
      error.value = msg
      throw e
    } finally {
      loading.value = false
    }
  }

  async function joinLeague(inviteCode: string) {
    loading.value = true
    error.value = null
    try {
      const result = await api.joinLeague(inviteCode)
      return result
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro ao entrar na liga'
      error.value = msg
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createPrediction(data: {
    fight_id: string
    predicted_winner_id: string
    predicted_method?: string
    predicted_round?: number
  }) {
    loading.value = true
    error.value = null
    try {
      const pred = await api.createPrediction(data)
      predictions.value.push(pred)
      return pred
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro ao criar predição'
      error.value = msg
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    predictions,
    leaderboard,
    achievements,
    leagues,
    loading,
    error,
    fetchPredictions,
    fetchLeaderboard,
    fetchAchievements,
    fetchLeagues,
    createLeague,
    joinLeague,
    createPrediction,
  }
})
