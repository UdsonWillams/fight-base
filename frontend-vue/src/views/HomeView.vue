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
        <div v-for="sim in simulationStore.recentSimulations" :key="sim.id" class="glass-card p-4">
          <div class="flex items-center justify-between gap-4">
            <div class="flex-1 text-right">
              <span :class="sim.winner_id === sim.fighter1_id ? 'text-green-400 font-semibold' : 'text-white/70'">
                {{ sim.fighter1_name }}
              </span>
            </div>
            <div class="flex-shrink-0 text-center">
              <span class="text-sm font-bold text-white/30">VS</span>
            </div>
            <div class="flex-1">
              <span :class="sim.winner_id === sim.fighter2_id ? 'text-green-400 font-semibold' : 'text-white/70'">
                {{ sim.fighter2_name }}
              </span>
            </div>
          </div>
          <div class="mt-2 text-center text-sm text-white/40">
            {{ sim.winner_name }} venceu por {{ sim.method_details }} no R{{ sim.finish_round }}
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
