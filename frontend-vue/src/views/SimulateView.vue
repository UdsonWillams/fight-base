<template>
  <div class="page-container">
    <h1 class="section-title">{{ t('simulate.title') }}</h1>

    <div v-if="!authStore.isLoggedIn" class="glass-card p-8 text-center max-w-lg mx-auto mb-10">
      <div class="text-4xl mb-4">&#x1F512;</div>
      <h2 class="text-xl font-semibold text-white mb-2">Login necessario</h2>
      <p class="text-white/50 mb-6">Voce precisa estar logado para simular lutas.</p>
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

      <div class="glass-card p-6 text-center max-w-md mx-auto mb-10">
        <div class="flex items-center justify-center gap-4 mb-6">
          <span class="text-sm font-medium text-white/60">{{ t('simulate.rounds') }}</span>
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
        <SimulationResult :result="simulationStore.result" :fighter1="fighter1" :fighter2="fighter2" />
      </div>

      <section v-if="simulationStore.recentSimulations.length > 0" class="recent-sims">
        <h2 class="text-2xl font-bold text-white/80 mb-6">{{ t('app.recentSimulations') }}</h2>
        <div class="space-y-3">
          <div v-for="sim in simulationStore.recentSimulations" :key="sim.id" class="glass-card p-4">
            <div class="flex items-center justify-between gap-4">
              <span class="text-sm text-white/30">{{ new Date(sim.created_at).toLocaleDateString('pt-BR') }}</span>
              <div class="flex items-center gap-4">
                <span class="font-semibold text-sm" :class="sim.winner_id === sim.fighter1_id ? 'text-green-400' : 'text-white/50'">{{ sim.fighter1_name }}</span>
                <span class="text-xs text-white/20">VS</span>
                <span class="font-semibold text-sm" :class="sim.winner_id === sim.fighter2_id ? 'text-green-400' : 'text-white/50'">{{ sim.fighter2_name }}</span>
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
import { ref, onMounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import FighterSelector from '@/components/ui/FighterSelector.vue'
import VsDisplay from '@/components/ui/VsDisplay.vue'
import SimulationResult from '@/components/simulation/SimulationResult.vue'
import { useAuthStore } from '@/stores/auth'
import { useSimulationStore } from '@/stores/simulation'
import type { Fighter } from '@/types'

const { t } = useI18n()
const toast = useToast()
const authStore = useAuthStore()
const simulationStore = useSimulationStore()

const fighter1 = ref<Fighter | null>(null)
const fighter2 = ref<Fighter | null>(null)
const rounds = ref(5)
const resultSection = ref<HTMLElement | null>(null)

async function simulateFight() {
  if (!fighter1.value || !fighter2.value) return
  try {
    await simulationStore.runSimulation(fighter1.value.id, fighter2.value.id, rounds.value)
    await nextTick()
    resultSection.value?.scrollIntoView({ behavior: 'smooth' })
  } catch {
    toast.add({ severity: 'error', summary: t('common.error'), detail: simulationStore.error || t('common.error'), life: 5000 })
  }
}

onMounted(() => {
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
