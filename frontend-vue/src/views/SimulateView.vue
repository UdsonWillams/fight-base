<template>
  <div class="page-container">
    <h1 class="section-title">{{ t('simulate.title') }}</h1>

    <div v-if="!authStore.isLoggedIn" class="glass-card p-8 text-center max-w-lg mx-auto mb-10">
      <div class="text-4xl mb-4">🔒</div>
      <h2 class="text-xl font-semibold text-white mb-2">Login necessario</h2>
      <p class="text-white/60 mb-6">Voce precisa estar logado para simular lutas.</p>
      <div class="flex gap-3 justify-center">
        <router-link to="/login" class="glass-button primary !px-6 !py-2 !rounded-xl">Entrar</router-link>
        <router-link to="/register" class="glass-button !px-6 !py-2 !rounded-xl">Criar Conta</router-link>
      </div>
    </div>

    <template v-else>
      <div class="sim-setup">
        <div class="sim-fighter-col">
          <FighterSelector v-model="fighter1" :label="t('simulate.selectFighter1')" :placeholder="t('fighters.search')" />
        </div>
        <div class="sim-vs-col">
          <VsDisplay :fighter1="fighter1" :fighter2="fighter2" />
        </div>
        <div class="sim-fighter-col">
          <FighterSelector v-model="fighter2" :label="t('simulate.selectFighter2')" :placeholder="t('fighters.search')" />
        </div>
      </div>

      <!-- Predição automática -->
      <div v-if="fighter1 && fighter2" class="prediction-panel glass-card p-6 text-center max-w-lg mx-auto mb-8">
        <h3 class="prediction-title">Analise do Modelo</h3>

        <div v-if="predictionLoading" class="animate-pulse flex flex-col items-center gap-3">
          <div class="h-4 bg-white/10 rounded w-48" />
          <div class="h-3 bg-white/8 rounded w-64" />
          <div class="h-2 bg-white/5 rounded w-full mt-2" />
        </div>

        <div v-else-if="predictionError" class="text-red-400 text-sm">
          {{ predictionError }}
        </div>

        <template v-else-if="prediction">
          <div class="prediction-bar-container">
            <div class="prediction-side">
              <span class="prediction-name">{{ fighter1.name }}</span>
              <span class="prediction-value" :class="{ 'prob-high': prediction.fighter1_win_probability >= 50 }">
                {{ Math.round(prediction.fighter1_win_probability) }}%
              </span>
            </div>
            <div class="prediction-track">
              <div class="prediction-fill" :style="{ width: `${prediction.fighter1_win_probability}%` }" />
            </div>
            <div class="prediction-side">
              <span class="prediction-name">{{ fighter2.name }}</span>
              <span class="prediction-value" :class="{ 'prob-high': prediction.fighter2_win_probability >= 50 }">
                {{ Math.round(prediction.fighter2_win_probability) }}%
              </span>
            </div>
          </div>

          <div class="prediction-analysis">
            <p class="analysis-text">{{ prediction.analysis }}</p>
            <div class="advantages">
              <span v-if="prediction.overall_advantage" class="advantage-badge">
                {{ prediction.overall_advantage }} e o favorito
              </span>
            </div>
          </div>

          <div class="result-probabilities">
            <span class="prob-tag ko">KO: {{ Math.round(prediction.ko_probability) }}%</span>
            <span class="prob-tag sub">Sub: {{ Math.round(prediction.submission_probability) }}%</span>
            <span class="prob-tag dec">Dec: {{ Math.round(prediction.decision_probability) }}%</span>
          </div>
        </template>
      </div>

      <div class="glass-card p-6 text-center max-w-md mx-auto mb-10">
        <div class="flex items-center justify-center gap-4 mb-6">
          <span class="text-sm font-medium text-white/70">{{ t('simulate.rounds') }}</span>
          <div class="flex gap-2">
            <button v-for="r in [3, 5]" :key="r" class="glass-button text-sm !py-2 !px-6" :class="{ primary: rounds === r }" @click="rounds = r">{{ r }}</button>
          </div>
        </div>
        <button class="glass-button primary w-full !py-4 !text-lg !rounded-xl" :disabled="!fighter1 || !fighter2 || simulationStore.simulating" @click="simulateFight">
          <span v-if="simulationStore.simulating" class="flex items-center justify-center gap-2">
            <svg class="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
            {{ t('common.loading') }}
          </span>
          <span v-else>{{ t('simulate.simulate') }}</span>
        </button>
      </div>

      <div v-if="simulationStore.result" ref="resultSection" class="mb-12">
        <SimulationResult :result="simulationStore.result" :fighter1="fighter1" :fighter2="fighter2" @simulate-again="resetSimulation" />
      </div>

      <section v-if="simulationStore.recentSimulations.length > 0" class="recent-sims">
        <h2 class="text-2xl font-bold text-white/80 mb-6">{{ t('app.recentSimulations') }}</h2>
        <div class="space-y-3">
          <div v-for="sim in simulationStore.recentSimulations" :key="sim.id" class="glass-card p-4">
            <div class="flex items-center justify-between gap-4">
              <span class="text-sm text-white/40">{{ new Date(sim.created_at).toLocaleDateString('pt-BR') }}</span>
              <div class="flex items-center gap-4">
                <span class="font-semibold text-sm" :class="sim.winner_id === sim.fighter1_id ? 'text-green-400' : 'text-white/60'">{{ sim.fighter1_name }}</span>
                <span class="text-xs text-white/30">VS</span>
                <span class="font-semibold text-sm" :class="sim.winner_id === sim.fighter2_id ? 'text-green-400' : 'text-white/60'">{{ sim.fighter2_name }}</span>
              </div>
              <span class="text-sm text-purple-400">{{ sim.result_type }}</span>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import FighterSelector from '@/components/ui/FighterSelector.vue'
import VsDisplay from '@/components/ui/VsDisplay.vue'
import SimulationResult from '@/components/simulation/SimulationResult.vue'
import { useAuthStore } from '@/stores/auth'
import { useSimulationStore } from '@/stores/simulation'
import { api } from '@/services/api'
import type { Fighter } from '@/types'

const { t } = useI18n()
const toast = useToast()
const authStore = useAuthStore()
const simulationStore = useSimulationStore()

const fighter1 = ref<Fighter | null>(null)
const fighter2 = ref<Fighter | null>(null)
const rounds = ref(5)
const resultSection = ref<HTMLElement | null>(null)

const prediction = ref<any>(null)
const predictionLoading = ref(false)
const predictionError = ref<string | null>(null)

async function fetchPrediction() {
  if (!fighter1.value || !fighter2.value) {
    prediction.value = null
    return
  }

  predictionLoading.value = true
  predictionError.value = null
  try {
    const result = await api.predictFight(fighter1.value.id, fighter2.value.id)
    prediction.value = result
  } catch (err) {
    predictionError.value = err instanceof Error ? err.message : 'Erro ao buscar predição'
    prediction.value = null
  } finally {
    predictionLoading.value = false
  }
}

watch([fighter1, fighter2], () => {
  if (fighter1.value?.id && fighter2.value?.id) {
    fetchPrediction()
  } else {
    prediction.value = null
  }
})

async function simulateFight() {
  if (!fighter1.value || !fighter2.value) return
  try {
    await simulationStore.runSimulation(fighter1.value.id, fighter2.value.id, rounds.value)
    await nextTick()
    resultSection.value?.scrollIntoView({ behavior: 'smooth' })
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err)
    const isServerError = msg.includes('500') || msg.includes('Internal Server Error')
    const detail = isServerError
      ? 'Servico de simulacao temporariamente indisponivel. Tente novamente mais tarde.'
      : (simulationStore.error || t('common.error'))
    toast.add({ severity: 'error', summary: t('common.error'), detail, life: 5000 })
  }
}

function resetSimulation() {
  simulationStore.clearResult()
}

onMounted(async () => {
  await authStore.checkAuth()
  simulationStore.fetchRecentSimulations(10)
})
</script>

<style scoped>
.sim-setup {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 24px;
  align-items: start;
  margin-bottom: 32px;
}

.sim-fighter-col {
  display: flex;
  flex-direction: column;
}

.sim-vs-col {
  display: flex;
  align-items: center;
  justify-content: center;
  padding-top: 28px;
}

.prediction-panel {
  transition: all 0.3s ease;
}

.prediction-title {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 16px;
}

.prediction-bar-container {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.prediction-side {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  min-width: 80px;
}

.prediction-name {
  font-size: 0.75rem;
  color: var(--text-secondary);
  white-space: nowrap;
  text-align: center;
  font-weight: 500;
}

.prediction-value {
  font-size: 1.3rem;
  font-weight: 800;
  color: var(--text-secondary);
}

.prediction-value.prob-high {
  color: #22c55e;
}

.prediction-track {
  flex: 1;
  height: 14px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 7px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.prediction-fill {
  height: 100%;
  background: linear-gradient(90deg, #ef4444, #eab308, #22c55e);
  border-radius: 7px;
  transition: width 0.8s ease;
}

.prediction-analysis {
  margin-bottom: 14px;
}

.analysis-text {
  font-size: 0.9rem;
  color: var(--text-primary);
  font-weight: 500;
  margin-bottom: 8px;
  line-height: 1.5;
}

.advantages {
  display: flex;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}

.advantage-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
  background: rgba(234, 179, 8, 0.1);
  color: #eab308;
  border: 1px solid rgba(234, 179, 8, 0.2);
}

.result-probabilities {
  display: flex;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}

.prob-tag {
  padding: 3px 10px;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 600;
}

.prob-tag.ko {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
}

.prob-tag.sub {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
}

.prob-tag.dec {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
}

.recent-sims {
  max-width: 700px;
  margin: 0 auto;
}

@media (max-width: 1024px) {
  .sim-setup {
    grid-template-columns: 1fr;
  }
  .sim-vs-col {
    padding-top: 0;
  }
}
</style>
