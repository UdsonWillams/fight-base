<template>
  <div class="simulation-result">
    <div class="winner-section glass-card">
      <div class="winner-crown">&#x1F451;</div>
      <h2 class="winner-name">{{ result.winner_name || '???' }}</h2>
      <div class="winner-details">
        <span class="method-badge" :class="'method-' + result.method_details?.toLowerCase()">
          {{ t(`simulation.${result.method_details?.toLowerCase()}`) || result.method_details }}
        </span>
        <span v-if="result.finish_round" class="round-info">Round {{ result.finish_round }}</span>
        <span v-if="result.finish_time" class="time-info">{{ result.finish_time }}</span>
      </div>
    </div>

    <div class="probability-section glass-card">
      <h3 class="section-title">{{ t('simulation.winProbability') }}</h3>
      <div class="prob-bar-container">
        <div class="prob-side left">
          <span class="prob-name">{{ fighter1?.name || t('simulation.fighter1') }}</span>
          <span class="prob-value" :class="{ 'prob-high': winProb1 >= 50 }">{{ winProb1 }}%</span>
        </div>
        <div class="prob-track">
          <div class="prob-fill" :style="{ width: `${winProb1}%` }" />
        </div>
        <div class="prob-side right">
          <span class="prob-name">{{ fighter2?.name || t('simulation.fighter2') }}</span>
          <span class="prob-value" :class="{ 'prob-high': winProb2 >= 50 }">{{ winProb2 }}%</span>
        </div>
      </div>
    </div>

    <div v-if="result.simulation_details && result.simulation_details.length > 0" class="rounds-section glass-card">
      <h3 class="section-title">{{ t('simulation.roundDetails') }}</h3>
      <RoundAnimation :roundDetails="result.simulation_details" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import RoundAnimation from './RoundAnimation.vue'
import type { Fighter, SimulationResult } from '@/types'

const { t } = useI18n()

const props = defineProps<{
  result: SimulationResult
  fighter1: Fighter | null
  fighter2: Fighter | null
}>()

const winProb1 = computed(() => {
  return Math.round(props.result.fighter1_probability * 100)
})

const winProb2 = computed(() => Math.round(props.result.fighter2_probability * 100))
</script>

<style scoped>
.simulation-result {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 700px;
  margin: 0 auto;
}

.winner-section {
  padding: 2rem;
  text-align: center;
}

.winner-crown {
  font-size: 2.5rem;
  margin-bottom: 8px;
}

.winner-name {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--gold-light);
  margin-bottom: 10px;
}

.winner-details {
  display: flex;
  justify-content: center;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.method-badge {
  padding: 4px 14px;
  border-radius: 16px;
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
}

.method-ko, .method-knockout {
  background: rgba(239, 68, 68, 0.2);
  color: var(--danger);
}

.method-submission {
  background: rgba(16, 185, 129, 0.2);
  color: var(--success);
}

.method-decision {
  background: rgba(59, 130, 246, 0.2);
  color: var(--primary-light);
}

.method-draw {
  background: rgba(245, 158, 11, 0.2);
  color: var(--gold-light);
}

.round-info, .time-info {
  font-size: 0.85rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.section-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 14px;
}

.probability-section {
  padding: 1.25rem 1.5rem;
}

.prob-bar-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.prob-side {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  min-width: 80px;
}

.prob-name {
  font-size: 0.75rem;
  color: var(--text-secondary);
  white-space: nowrap;
  text-align: center;
}

.prob-value {
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--text-muted);
}

.prob-value.prob-high {
  color: var(--success);
}

.prob-track {
  flex: 1;
  height: 12px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 6px;
  overflow: hidden;
}

.prob-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--accent));
  border-radius: 6px;
  transition: width 0.8s ease;
}

.rounds-section {
  padding: 1.25rem 1.5rem;
}
</style>
