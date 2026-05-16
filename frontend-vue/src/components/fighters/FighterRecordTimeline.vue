<template>
  <div class="record-timeline">
    <div v-if="parsedCartel.length > 0" class="record-summary mb-6">
      <div class="summary-card wins">
        <div class="summary-value">{{ wins }}</div>
        <div class="summary-label">Vitorias</div>
      </div>
      <div class="summary-card losses">
        <div class="summary-value">{{ losses }}</div>
        <div class="summary-label">Derrotas</div>
      </div>
      <div class="summary-card draws">
        <div class="summary-value">{{ draws }}</div>
        <div class="summary-label">Empates</div>
      </div>
    </div>

    <div v-if="parsedCartel.length > 0" class="timeline">
      <div
        v-for="(fight, index) in parsedCartel"
        :key="index"
        class="timeline-item"
        :class="{ 'last-item': index === parsedCartel.length - 1 }"
      >
        <div class="timeline-marker" :class="resultClass(fight.result)">
          <span class="marker-icon">{{ resultIcon(fight.result) }}</span>
        </div>
        <div class="timeline-card glass-card">
          <div class="card-header">
            <div class="header-left">
              <span class="corner-badge" :class="cornerClass(fight.corner)">
                {{ fight.corner || '?' }}
              </span>
              <span class="fight-date">{{ fight.date }}</span>
            </div>
            <span class="fight-org">{{ fight.organization }}</span>
          </div>

          <div class="card-body">
            <!-- Opção B: Mostrar ambos os corners -->
            <div class="fight-matchup">
              <div class="fighter-block" :class="{ 'is-winner': fight.result === 'W' }">
                <span class="fighter-label" :class="cornerClass(fight.corner)">
                  {{ fight.corner === 'Red' ? '🟥' : fight.corner === 'Blue' ? '🟦' : '•' }}
                  {{ fight.corner || '?' }}
                </span>
                <span class="fighter-name">{{ fighterName }}</span>
              </div>
              <span class="vs-text">VS</span>
              <div class="fighter-block" :class="{ 'is-winner': fight.result === 'L' }">
                <span class="fighter-label" :class="cornerClass(opponentCorner(fight.corner))">
                  {{ opponentCorner(fight.corner) === 'Red' ? '🟥' : opponentCorner(fight.corner) === 'Blue' ? '🟦' : '•' }}
                  {{ opponentCorner(fight.corner) || '?' }}
                </span>
                <span class="fighter-name opponent-name">{{ fight.opponent }}</span>
              </div>
            </div>

            <div class="details-row">
              <span class="detail-badge method">{{ fight.method }}</span>
              <span class="detail-badge round">R{{ fight.round }}</span>
              <span class="detail-badge result" :class="resultClass(fight.result)">
                {{ fight.result === 'W' ? 'Vitoria' : fight.result === 'L' ? 'Derrota' : 'Empate' }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty-state !py-8">
      <p class="text-sm">Nenhum historico de lutas registrado.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  cartel: string | any[]
  fighterName?: string
}>()

const parsedCartel = computed(() => {
  if (!props.cartel) return []
  if (Array.isArray(props.cartel)) return props.cartel
  try {
    const parsed = JSON.parse(props.cartel)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
})

const wins = computed(() => parsedCartel.value.filter(f => f.result === 'W').length)
const losses = computed(() => parsedCartel.value.filter(f => f.result === 'L').length)
const draws = computed(() => parsedCartel.value.filter(f => f.result === 'D' || f.result === 'Draw').length)

function resultClass(result: string): string {
  const r = (result || '').toUpperCase()
  if (r === 'W') return 'win'
  if (r === 'L') return 'loss'
  return 'draw'
}

function resultIcon(result: string): string {
  const r = (result || '').toUpperCase()
  if (r === 'W') return '✓'
  if (r === 'L') return '✕'
  return '='
}

function cornerClass(corner: string): string {
  const c = (corner || '').toLowerCase()
  if (c === 'red') return 'corner-red'
  if (c === 'blue') return 'corner-blue'
  return 'corner-unknown'
}

function opponentCorner(fighterCorner: string): string {
  const c = (fighterCorner || '').toLowerCase()
  if (c === 'red') return 'Blue'
  if (c === 'blue') return 'Red'
  return ''
}
</script>

<style scoped>
.record-timeline {
  max-width: 700px;
  margin: 0 auto;
}

.record-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.summary-card {
  text-align: center;
  padding: 16px 8px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--glass-border);
}

.summary-card.wins .summary-value {
  color: #22c55e;
}

.summary-card.losses .summary-value {
  color: #ef4444;
}

.summary-card.draws .summary-value {
  color: #eab308;
}

.summary-value {
  font-size: 2rem;
  font-weight: 800;
  line-height: 1;
}

.summary-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.timeline {
  position: relative;
  padding-left: 24px;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 15px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: linear-gradient(180deg, var(--primary), var(--accent));
  opacity: 0.3;
}

.timeline-item {
  position: relative;
  margin-bottom: 16px;
}

.timeline-item.last-item {
  margin-bottom: 0;
}

.timeline-marker {
  position: absolute;
  left: -24px;
  top: 12px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 700;
  z-index: 2;
  border: 2px solid;
}

.timeline-marker.win {
  background: rgba(34, 197, 94, 0.15);
  border-color: #22c55e;
  color: #22c55e;
}

.timeline-marker.loss {
  background: rgba(239, 68, 68, 0.15);
  border-color: #ef4444;
  color: #ef4444;
}

.timeline-marker.draw {
  background: rgba(234, 179, 8, 0.15);
  border-color: #eab308;
  color: #eab308;
}

.timeline-card {
  padding: 14px 16px;
  margin-left: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--glass-border);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.corner-badge {
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.65rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.corner-badge.corner-red {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
}

.corner-badge.corner-blue {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
}

.corner-badge.corner-unknown {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-muted);
}

.fight-date {
  font-size: 0.8rem;
  color: var(--text-muted);
  font-weight: 500;
}

.fight-org {
  font-size: 0.7rem;
  color: var(--accent-light);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.fight-matchup {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 10px;
}

.fighter-block {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 4px;
  padding: 6px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.fighter-block.is-winner {
  background: rgba(234, 179, 8, 0.08);
  border: 1px solid rgba(234, 179, 8, 0.15);
}

.fighter-label {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 2px 8px;
  border-radius: 6px;
}

.fighter-label.corner-red {
  color: #f87171;
  background: rgba(239, 68, 68, 0.1);
}

.fighter-label.corner-blue {
  color: #60a5fa;
  background: rgba(59, 130, 246, 0.1);
}

.fighter-name {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.opponent-name {
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--text-primary);
}

.vs-text {
  font-size: 0.8rem;
  font-weight: 900;
  color: var(--text-muted);
  letter-spacing: 2px;
  flex-shrink: 0;
}

.details-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}

.detail-badge {
  padding: 3px 10px;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 600;
}

.detail-badge.method {
  background: rgba(124, 58, 237, 0.15);
  color: var(--accent-light);
}

.detail-badge.round {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
}

.detail-badge.result {
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-badge.result.win {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.detail-badge.result.loss {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.detail-badge.result.draw {
  background: rgba(234, 179, 8, 0.15);
  color: #eab308;
}

@media (max-width: 640px) {
  .record-summary {
    grid-template-columns: 1fr;
  }
  .fight-matchup {
    flex-direction: column;
    gap: 6px;
  }
  .vs-text {
    order: -1;
  }
}
</style>
