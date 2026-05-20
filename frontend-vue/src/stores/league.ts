import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/services/api'
import type { League, LeagueDetail, LeagueLeaderboardEntry, LeaguePrediction } from '@/types'

export const useLeagueStore = defineStore('league', () => {
  const leagues = ref<League[]>([])
  const currentLeague = ref<LeagueDetail | null>(null)
  const leaderboard = ref<LeagueLeaderboardEntry[]>([])
  const predictions = ref<LeaguePrediction[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchLeagues() {
    loading.value = true
    error.value = null
    try {
      leagues.value = await api.getMyLeagues()
    } catch (e: any) {
      error.value = e.message || 'Erro ao carregar ligas'
    } finally {
      loading.value = false
    }
  }

  async function fetchLeague(id: string) {
    loading.value = true
    error.value = null
    try {
      currentLeague.value = await api.getLeague(id)
      return currentLeague.value
    } catch (e: any) {
      error.value = e.message || 'Erro ao carregar liga'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createLeague(data: { name: string; description?: string }) {
    loading.value = true
    error.value = null
    try {
      const league = await api.createLeague(data)
      leagues.value.unshift(league)
      return league
    } catch (e: any) {
      error.value = e.message || 'Erro ao criar liga'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function joinLeague(inviteCode: string) {
    loading.value = true
    error.value = null
    try {
      await api.joinLeague(inviteCode)
      await fetchLeagues()
    } catch (e: any) {
      error.value = e.message || 'Erro ao entrar na liga'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteLeague(id: string) {
    loading.value = true
    error.value = null
    try {
      await api.deleteLeague(id)
      leagues.value = leagues.value.filter((l) => l.id !== id)
      currentLeague.value = null
    } catch (e: any) {
      error.value = e.message || 'Erro ao deletar liga'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function selectEvent(leagueId: string, eventId: string) {
    loading.value = true
    error.value = null
    try {
      await api.selectLeagueEvent(leagueId, eventId)
      await fetchLeague(leagueId)
    } catch (e: any) {
      error.value = e.message || 'Erro ao selecionar evento'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchLeaderboard(leagueId: string) {
    loading.value = true
    error.value = null
    try {
      leaderboard.value = await api.getLeagueLeaderboard(leagueId)
    } catch (e: any) {
      error.value = e.message || 'Erro ao carregar ranking'
    } finally {
      loading.value = false
    }
  }

  async function submitPredictions(leagueId: string, preds: { fight_id: string; predicted_winner_id: string | null; predicted_method_id?: string | null; predicted_round?: number | null }[]) {
    loading.value = true
    error.value = null
    try {
      predictions.value = await api.createLeaguePredictions(leagueId, preds)
    } catch (e: any) {
      error.value = e.message || 'Erro ao salvar palpites'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchMyPredictions(leagueId: string) {
    loading.value = true
    error.value = null
    try {
      predictions.value = await api.getMyLeaguePredictions(leagueId)
    } catch (e: any) {
      error.value = e.message || 'Erro ao carregar palpites'
    } finally {
      loading.value = false
    }
  }

  async function leaveLeagueFn(leagueId: string) {
    loading.value = true
    error.value = null
    try {
      await api.leaveLeague(leagueId)
      leagues.value = leagues.value.filter((l) => l.id !== leagueId)
      currentLeague.value = null
    } catch (e: any) {
      error.value = e.message || 'Erro ao sair da liga'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createFighter(leagueId: string, data: any) {
    loading.value = true
    error.value = null
    try {
      const result = await api.createLeagueFighter(leagueId, data)
      await fetchLeaderboard(leagueId)
      await fetchLeague(leagueId)
      return result
    } catch (e: any) {
      error.value = e.message || 'Erro ao criar lutador'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function upgradeFighter(leagueId: string, fighterId: string, attribute: string, pointsCost: number) {
    loading.value = true
    error.value = null
    try {
      const result = await api.upgradeLeagueFighter(leagueId, fighterId, { attribute, points_cost: pointsCost })
      await fetchLeaderboard(leagueId)
      return result
    } catch (e: any) {
      error.value = e.message || 'Erro ao melhorar lutador'
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    leagues,
    currentLeague,
    leaderboard,
    predictions,
    loading,
    error,
    fetchLeagues,
    fetchLeague,
    createLeague,
    joinLeague,
    deleteLeague,
    selectEvent,
    fetchLeaderboard,
    submitPredictions,
    fetchMyPredictions,
    leaveLeague: leaveLeagueFn,
    createFighter,
    upgradeFighter,
  }
})
