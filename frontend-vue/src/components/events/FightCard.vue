<template>
  <div class="fight-card glass-card">
    <div class="fight-content">
      <div class="fighter-side" :class="{ winner: isWinner(fighter1Name) }">
        <h4 class="f-name">{{ fighter1Name }}</h4>
        <div class="f-stats">
          <span class="f-overall" :style="{ color: getOverallColor(fighter1Overall) }">
            {{ fighter1Overall || '--' }}
          </span>
        </div>
      </div>

      <div class="vs-divider">
        <span class="vs-label">VS</span>
        <div v-if="fight?.is_title_fight" class="title-badge">&#x1F3C6; TITLE</div>
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
        <h4 class="f-name">{{ fighter2Name }}</h4>
        <div class="f-stats">
          <span class="f-overall" :style="{ color: getOverallColor(fighter2Overall) }">
            {{ fighter2Overall || '--' }}
          </span>
        </div>
      </div>
    </div>

    <div v-if="fight?.result_type && fight?.method_details" class="result-detail">
      <span class="font-semibold" :class="winnerColor">{{ fight.winner?.name || '' }}</span>
      <span>venceu por {{ fight.method_details }}</span>
      <span v-if="fight.finish_time">as {{ fight.finish_time }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Fight } from '@/types'

const props = defineProps<{
  fight?: Fight | null
  fighter1Name: string
  fighter2Name: string
  fighter1Overall: number
  fighter2Overall: number
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
}

.fight-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.fighter-side {
  flex: 1;
  text-align: center;
  padding: 6px 0;
}

.fighter-side.winner .f-name {
  color: var(--gold-light);
}

.f-name {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.f-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.f-overall {
  font-weight: 800;
  font-size: 1.1rem;
}

.vs-divider {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
  min-width: 56px;
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
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--glass-border);
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-weight: 500;
}
</style>
