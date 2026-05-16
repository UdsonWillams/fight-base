<template>
  <div class="simulation-result">
    <!-- Live Fight Animation -->
    <FightLiveAnimation
      v-if="showAnimation"
      :result="result"
      :fighter1="fighter1"
      :fighter2="fighter2"
      @simulate-again="$emit('simulateAgain')"
    />

    <!-- Static Result (fallback se não houver rounds) -->
    <template v-else>
      <div class="winner-section glass-card">
        <div class="winner-crown">👑</div>
        <h2 class="winner-name">{{ result.winner_name || '???' }}</h2>
        <div class="winner-details">
          <span class="method-badge" :class="'method-' + (result.method_details || result.result_type || '').toLowerCase()">
            {{ result.method_details || result.result_type || 'Desconhecido' }}
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

      <div class="rounds-section glass-card">
        <h3 class="section-title">Detalhes da Luta</h3>
        <div class="no-rounds-fallback">
          <p class="fallback-text">
            Luta finalizada por <strong>{{ result.method_details || result.result_type }}</strong>
            <span v-if="result.finish_round"> no Round {{ result.finish_round }}</span>
            <span v-if="result.finish_time"> ({{ result.finish_time }})</span>
          </p>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import FightLiveAnimation from './FightLiveAnimation.vue'
import type { Fighter, SimulationResult } from '@/types'

const { t } = useI18n()

const props = defineProps<{
  result: SimulationResult
  fighter1: Fighter | null
  fighter2: Fighter | null
}>()

const emit = defineEmits<{
  (e: 'simulateAgain'): void
}>()

const winProb1 = computed(() => {
  return Math.round((props.result.fighter1_probability || 0) * 100)
})

const winProb2 = computed(() => Math.round((props.result.fighter2_probability || 0) * 100))

const showAnimation = computed(() => {
  const details = props.result.simulation_details
  if (!details) return false
  const rounds = Array.isArray(details) ? details : (details.rounds || [])
  return rounds.length > 0
})
</script>

<style scoped>
.simulation-result {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 800px;
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

.method-ko, .method-knockout, .method-tko {
  background: rgba(239, 68, 68, 0.25);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.method-submission, .method-sub {
  background: rgba(16, 185, 129, 0.25);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.method-decision, .method-dec {
  background: rgba(59, 130, 246, 0.25);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.method-draw {
  background: rgba(234, 179, 8, 0.25);
  color: #fbbf24;
  border: 1px solid rgba(234, 179, 8, 0.3);
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
  gap: 4px;
  min-width: 80px;
}

.prob-name {
  font-size: 0.75rem;
  color: var(--text-secondary);
  white-space: nowrap;
  text-align: center;
  font-weight: 500;
}

.prob-value {
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--text-secondary);
}

.prob-value.prob-high {
  color: #22c55e;
}

.prob-track {
  flex: 1;
  height: 12px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.05);
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

.no-rounds-fallback {
  text-align: center;
  padding: 1rem 0;
}

.fallback-text {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.fallback-text strong {
  color: var(--text-primary);
}
</style>
