<template>
  <div class="page-container">
    <section class="text-center mb-12 pt-8">
      <h1 class="text-4xl md:text-6xl font-black tracking-tight mb-4">
        <span class="text-transparent bg-clip-text bg-gradient-to-r from-red-400 via-red-500 to-cyan-400">
          {{ t('app.nextGen') }}
        </span>
      </h1>
      <p class="text-lg text-white/50 max-w-2xl mx-auto mb-8">
        {{ t('app.subtitle') }}
      </p>
    </section>

    <section class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-16">
      <div class="glass-card p-6 text-center">
        <div v-if="loadingStats" class="animate-pulse space-y-4">
          <div class="h-12 bg-white/10 rounded w-20 mx-auto" />
        </div>
        <template v-else>
          <div class="stat-value">{{ fighterCount }}</div>
          <div class="text-sm text-white/40 uppercase tracking-wider mt-2">{{ t('app.totalFighters') }}</div>
        </template>
      </div>
      <div class="glass-card p-6 text-center">
        <div v-if="loadingStats" class="animate-pulse space-y-4">
          <div class="h-12 bg-white/10 rounded w-20 mx-auto" />
        </div>
        <template v-else>
          <div class="stat-value">{{ totalSimulations }}</div>
          <div class="text-sm text-white/40 uppercase tracking-wider mt-2">{{ t('app.totalSimulations') }}</div>
        </template>
      </div>
    </section>

    <section class="glass-card p-8 mb-16 max-w-4xl mx-auto">
      <h2 class="text-2xl font-bold text-white mb-6">Como funciona o FightBase</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="text-center">
          <div class="text-4xl mb-3">🗂️</div>
          <h3 class="font-semibold text-white mb-2">Base de Lutadores</h3>
          <p class="text-sm text-white/50">Explore milhares de lutadores reais e crie seus proprios. Compare atributos como striking, grappling e muito mais.</p>
        </div>
        <div class="text-center">
          <div class="text-4xl mb-3">⚔️</div>
          <h3 class="font-semibold text-white mb-2">Simulacao de Lutas</h3>
          <p class="text-sm text-white/50">Escolha dois lutadores e simule um combate round a round com IA. Veja probabilidades e detalhes da luta.</p>
        </div>
        <div class="text-center">
          <div class="text-4xl mb-3">🏆</div>
          <h3 class="font-semibold text-white mb-2">Eventos e Palpites</h3>
          <p class="text-sm text-white/50">Crie eventos, monte cards de lutas e faca seus palpites. Compita com amigos nas ligas privadas.</p>
        </div>
      </div>
    </section>

    <section class="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
      <router-link to="/fighters" class="glass-button primary text-center !text-lg !py-4 !px-8 !rounded-xl w-full sm:w-auto hover:!scale-105 transition-transform">
        {{ t('app.exploreFighters') }}
      </router-link>
      <router-link to="/simulate" class="glass-button text-center !text-lg !py-4 !px-8 !rounded-xl w-full sm:w-auto hover:!scale-105 transition-transform">
        {{ t('app.simulateFight') }}
      </router-link>
    </section>

    <section v-if="simulationStore.recentSimulations.length > 0" class="mb-8">
      <h2 class="text-2xl font-bold text-white/80 mb-6">{{ t('app.recentSimulations') }}</h2>
      <div class="space-y-4 max-w-2xl mx-auto">
        <div
          v-for="sim in simulationStore.recentSimulations"
          :key="sim.id"
          class="sim-card glass-card p-5"
          :class="{ 'winner-left': sim.winner_id === sim.fighter1_id, 'winner-right': sim.winner_id === sim.fighter2_id }"
        >
          <div class="sim-header">
            <div class="fighter-block" :class="{ 'is-winner': sim.winner_id === sim.fighter1_id }">
              <span class="f-name">{{ sim.fighter1_name }}</span>
              <span v-if="sim.fighter1_probability != null" class="f-prob" :class="{ 'prob-high': sim.fighter1_probability >= 50 }">
                {{ Math.round(sim.fighter1_probability * 100) }}%
              </span>
            </div>
            <div class="vs-block">
              <span class="vs-text">VS</span>
            </div>
            <div class="fighter-block" :class="{ 'is-winner': sim.winner_id === sim.fighter2_id }">
              <span class="f-name">{{ sim.fighter2_name }}</span>
              <span v-if="sim.fighter2_probability != null" class="f-prob" :class="{ 'prob-high': sim.fighter2_probability >= 50 }">
                {{ Math.round(sim.fighter2_probability * 100) }}%
              </span>
            </div>
          </div>

          <div v-if="sim.fighter1_probability != null && sim.fighter2_probability != null" class="prob-track">
            <div class="prob-fill" :style="{ width: `${sim.fighter1_probability * 100}%` }" />
          </div>

          <div class="sim-result">
            <span class="winner-name">{{ sim.winner_name }}</span>
            <span class="result-text">
              venceu por <strong>{{ sim.method_details || sim.result_type }}</strong>
              <span v-if="sim.finish_round"> no Round {{ sim.finish_round }}</span>
            </span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useFighterStore } from '@/stores/fighters'
import { useSimulationStore } from '@/stores/simulation'

const { t } = useI18n()
const fighterStore = useFighterStore()
const simulationStore = useSimulationStore()

const fighterCount = ref(0)
const totalSimulations = ref(0)
const loadingStats = ref(true)

onMounted(async () => {
  try {
    await fighterStore.fetchStats()
    if (fighterStore.stats) fighterCount.value = fighterStore.stats.total_fighters
  } catch { /* stats optional */ }

  try {
    await simulationStore.fetchRecentSimulations(5)
  } catch { /* sims optional */ }

  loadingStats.value = false
})
</script>

<style scoped>
.stat-value {
  font-size: 3rem;
  font-weight: 800;
  color: var(--primary);
}

.sim-card {
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.sim-card:hover {
  transform: translateY(-2px);
}

.sim-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.fighter-block {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 4px;
  padding: 8px;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.fighter-block.is-winner {
  background: rgba(234, 179, 8, 0.08);
  border: 1px solid rgba(234, 179, 8, 0.2);
}

.fighter-block.is-winner .f-name {
  color: #eab308;
  font-weight: 800;
}

.f-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
  text-align: center;
}

.f-prob {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-weight: 600;
}

.f-prob.prob-high {
  color: #22c55e;
}

.vs-block {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.vs-text {
  font-size: 0.85rem;
  font-weight: 900;
  color: var(--text-muted);
  letter-spacing: 1px;
}

.prob-track {
  height: 6px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 12px;
}

.prob-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--accent));
  border-radius: 3px;
  transition: width 0.8s ease;
}

.sim-result {
  text-align: center;
  padding-top: 10px;
  border-top: 1px solid var(--glass-border);
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.winner-name {
  color: #eab308;
  font-weight: 700;
}

.result-text strong {
  color: var(--text-primary);
  font-weight: 600;
}

@media (max-width: 640px) {
  .sim-header {
    flex-direction: column;
    gap: 8px;
  }
  .vs-block {
    order: -1;
  }
}
</style>
