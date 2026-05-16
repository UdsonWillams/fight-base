<template>
  <div class="fight-card glass-card">
    <div class="fight-content">
      <div class="fighter-side" :class="{ winner: isWinner(fighter1Name) }">
        <div class="fighter-name-block">
          <h4 class="f-name">
            <FighterNameDisplay :name="fighter1Name" :nickname="fighter1Nickname" />
          </h4>
          <div class="f-overall" :style="{ color: getOverallColor(fighter1Overall) }">
            {{ fighter1Overall || '--' }}
          </div>
        </div>
        <div v-if="fighter1Probability != null" class="f-prob">
          {{ Math.round(fighter1Probability) }}%
        </div>
      </div>

      <div class="vs-divider">
        <span class="vs-label">VS</span>
        <div v-if="fight?.is_title_fight" class="title-badge">🏆 TITLE</div>
        <div v-if="fight?.weight_class" class="wc-label">{{ fight.weight_class }}</div>
        <div v-if="fight?.rounds" class="rounds-label">{{ fight.rounds }}R</div>
        <div v-if="fight?.result_type" class="result-mini">
          <span class="result-badge" :class="'result-' + (fight.result_type || '').toLowerCase()">
            {{ fight.result_type }}
          </span>
          <span v-if="fight.finish_round" class="result-round">R{{ fight.finish_round }}</span>
        </div>
      </div>

      <div class="fighter-side" :class="{ winner: isWinner2() }">
        <div class="fighter-name-block">
          <h4 class="f-name">
            <FighterNameDisplay :name="fighter2Name" :nickname="fighter2Nickname" />
          </h4>
          <div class="f-overall" :style="{ color: getOverallColor(fighter2Overall) }">
            {{ fighter2Overall || '--' }}
          </div>
        </div>
        <div v-if="fighter2Probability != null" class="f-prob">
          {{ Math.round(fighter2Probability) }}%
        </div>
      </div>
    </div>

    <div v-if="fight?.result_type && fight?.method_details" class="result-detail">
      <span class="font-semibold" :class="winnerColor">{{ fight.winner?.name || '' }}</span>
      <span>&nbsp;venceu por {{ fight.method_details }}</span>
      <span v-if="fight.finish_round">&nbsp;no R{{ fight.finish_round }}</span>
      <span v-if="fight.finish_time">&nbsp;({{ fight.finish_time }})</span>
    </div>

    <div v-if="fight?.fighter1_probability != null && fight?.fighter2_probability != null" class="prob-bar">
      <div class="prob-track">
        <div class="prob-fill" :style="{ width: `${fight.fighter1_probability}%` }" />
      </div>
      <div class="prob-labels">
        <span :class="{ 'prob-high': (fight.fighter1_probability || 0) >= 50 }">{{ Math.round(fight.fighter1_probability || 0) }}%</span>
        <span :class="{ 'prob-high': (fight.fighter2_probability || 0) >= 50 }">{{ Math.round(fight.fighter2_probability || 0) }}%</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import FighterNameDisplay from './FighterNameDisplay.vue'
import type { Fight } from '@/types'

const props = defineProps<{
  fight?: Fight | null
  fighter1Name: string
  fighter2Name: string
  fighter1Nickname?: string | null
  fighter2Nickname?: string | null
  fighter1Overall: number
  fighter2Overall: number
  fighter1Probability?: number | null
  fighter2Probability?: number | null
}>()

function isWinner(name: string): boolean {
  if (!props.fight?.winner_id) return false
  return (name === props.fighter1Name && props.fight.winner_id === props.fight.fighter1_id) ||
         (name === props.fighter2Name && props.fight.winner_id === props.fight.fighter2_id)
}

function isWinner2(): boolean {
  if (!props.fight?.winner_id) return false
  return props.fight.winner_id === props.fight.fighter2_id
}

const winnerColor = computed(() => {
  if (!props.fight?.winner) return 'text-white'
  return 'text-green-400'
})

function getOverallColor(overall: number): string {
  if (!overall) return 'var(--text-muted)'
  if (overall >= 90) return 'var(--gold)'
  if (overall >= 80) return 'var(--primary)'
  if (overall >= 65) return 'var(--accent)'
  return 'var(--text-muted)'
}
</script>

<style scoped>
.fight-card {
  padding: 1rem 1.25rem;
  position: relative;
  transition: all 0.3s ease;
}

.fight-card:hover {
  transform: translateY(-2px);
}

.fight-content {
  display: flex;
  align-items: stretch;
  gap: 12px;
}

.fighter-side {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 8px;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.fighter-side.winner {
  background: rgba(234, 179, 8, 0.08);
  border: 1px solid rgba(234, 179, 8, 0.2);
}

.fighter-name-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.f-name {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.3;
  text-align: center;
}

.f-overall {
  font-weight: 800;
  font-size: 1.5rem;
}

.f-prob {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 4px;
  font-weight: 600;
}

.vs-divider {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  flex-shrink: 0;
  min-width: 56px;
  padding: 4px 0;
}

.vs-label {
  font-size: 0.8rem;
  font-weight: 900;
  color: var(--text-muted);
}

.title-badge {
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 0.6rem;
  font-weight: 800;
  background: rgba(255, 215, 0, 0.15);
  color: var(--gold);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.wc-label {
  font-size: 0.65rem;
  color: var(--accent-light);
  text-transform: capitalize;
  font-weight: 600;
}

.rounds-label {
  font-size: 0.65rem;
  color: var(--text-muted);
  font-weight: 600;
}

.result-mini {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.result-badge {
  padding: 1px 8px;
  border-radius: 6px;
  font-size: 0.6rem;
  font-weight: 700;
  text-transform: uppercase;
}

.result-ko, .result-knockout, .result-technical_knockout {
  background: rgba(239, 68, 68, 0.2);
  color: var(--danger);
}

.result-submission, .result-sub {
  background: rgba(16, 185, 129, 0.2);
  color: var(--success);
}

.result-decision, .result-dec {
  background: rgba(59, 130, 246, 0.2);
  color: var(--primary-light);
}

.result-draw {
  background: rgba(245, 158, 11, 0.2);
  color: var(--gold);
}

.result-round {
  font-size: 0.65rem;
  color: var(--text-muted);
  font-weight: 600;
}

.result-detail {
  text-align: center;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--glass-border);
  font-size: 0.85rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.prob-bar {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--glass-border);
}

.prob-track {
  height: 8px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 4px;
  overflow: hidden;
}

.prob-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--accent));
  border-radius: 4px;
  transition: width 0.8s ease;
}

.prob-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  font-size: 0.7rem;
  color: var(--text-muted);
  font-weight: 600;
}

.prob-high {
  color: var(--success);
}

@media (max-width: 640px) {
  .fight-content {
    flex-direction: column;
    gap: 8px;
  }
  .vs-divider {
    flex-direction: row;
    gap: 8px;
    min-width: auto;
  }
}
</style>
