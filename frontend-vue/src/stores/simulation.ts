import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/services/api'
import type { Simulation, SimulationResult } from '@/types'

export const useSimulationStore = defineStore('simulation', () => {
  const result = ref<SimulationResult | null>(null)
  const recentSimulations = ref<Simulation[]>([])
  const simulating = ref(false)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function runSimulation(fighter1Id: string, fighter2Id: string, rounds: number = 5): Promise<void> {
    simulating.value = true
    error.value = null
    try {
      const simResult = await api.createSimulation({ fighter1_id: fighter1Id, fighter2_id: fighter2Id, rounds })
      result.value = simResult
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Erro desconhecido'
    } finally {
      simulating.value = false
    }
  }

  async function fetchRecentSimulations(limit: number = 10): Promise<void> {
    loading.value = true
    error.value = null
    try {
      recentSimulations.value = await api.getRecentSimulations(limit)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Erro desconhecido'
    } finally {
      loading.value = false
    }
  }

  function clearResult(): void {
    result.value = null
  }

  return {
    result,
    recentSimulations,
    simulating,
    loading,
    error,
    runSimulation,
    fetchRecentSimulations,
    clearResult,
  }
})
