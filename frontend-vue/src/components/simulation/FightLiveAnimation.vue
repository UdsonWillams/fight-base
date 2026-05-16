<template>
  <div class="fight-live-animation glass-card">
    <div class="fight-header">
      <div class="fighter-corner" :class="{ winner: result.winner_id === fighter1?.id }">
        <div class="corner-label red-corner">RED CORNER</div>
        <div class="fighter-photo">
          <img v-if="fighter1?.image_url" :src="fighter1.image_url" :alt="fighter1?.name" />
          <span v-else class="photo-fallback">🥊</span>
        </div>
        <h3 class="corner-name">
          <FighterNameDisplay :name="fighter1?.name || result.fighter1_name || 'Lutador 1'" :nickname="fighter1?.nickname" />
        </h3>
        <div class="momentum-bar">
          <div class="momentum-fill" :style="{ width: momentum1 + '%' }" />
        </div>
        <div class="corner-stats">
          <div class="stat-box">
            <small>Score</small>
            <span>{{ f1Score.toFixed(1) }}</span>
          </div>
          <div class="stat-box">
            <small>Pontos</small>
            <span>{{ f1TotalPoints }}</span>
          </div>
        </div>
        <div class="probability-badge">
          Predicao: {{ Math.round(result.fighter1_probability || 0) }}%
        </div>
      </div>

      <div class="fight-status">
        <div class="round-indicator" :class="roundStatusClass">{{ roundStatusText }}</div>
        <div class="time-bar-container">
          <div class="time-bar" :style="{ width: timeBarWidth + '%', transition: timeBarTransition }" />
        </div>
        <div class="live-badge">LIVE SIMULATION</div>
      </div>

      <div class="fighter-corner" :class="{ winner: result.winner_id === fighter2?.id }">
        <div class="corner-label blue-corner">BLUE CORNER</div>
        <div class="fighter-photo">
          <img v-if="fighter2?.image_url" :src="fighter2.image_url" :alt="fighter2?.name" />
          <span v-else class="photo-fallback">🥊</span>
        </div>
        <h3 class="corner-name">
          <FighterNameDisplay :name="fighter2?.name || result.fighter2_name || 'Lutador 2'" :nickname="fighter2?.nickname" />
        </h3>
        <div class="momentum-bar">
          <div class="momentum-fill" :style="{ width: momentum2 + '%' }" />
        </div>
        <div class="corner-stats">
          <div class="stat-box">
            <small>Score</small>
            <span>{{ f2Score.toFixed(1) }}</span>
          </div>
          <div class="stat-box">
            <small>Pontos</small>
            <span>{{ f2TotalPoints }}</span>
          </div>
        </div>
        <div class="probability-badge prob-right">
          Predicao: {{ Math.round(result.fighter2_probability || 0) }}%
        </div>
      </div>
    </div>

    <!-- Round Cards -->
    <div class="round-cards-area">
      <div
        v-for="(rc, idx) in completedRounds"
        :key="'round-' + rc.round_number"
        class="round-card completed"
      >
        <div class="round-card-header">
          <span class="round-card-title">ROUND {{ rc.round_number }}</span>
          <span class="round-card-score">
            <span class="f1-color">{{ rc.f1_pts.toFixed(1) }}</span>
            —
            <span class="f2-color">{{ rc.f2_pts.toFixed(1) }}</span>
          </span>
        </div>
        <div class="round-card-events">
          <div
            v-for="(evt, eIdx) in rc.events"
            :key="eIdx"
            class="fight-event"
            :class="{ 'critical-event': evt.isCritical }"
          >
            <span class="event-icon">{{ evt.emoji }}</span>
            <span class="event-text">{{ evt.text }}</span>
          </div>
        </div>
      </div>

      <!-- Current round being animated -->
      <div v-if="currentRoundCard" class="round-card active">
        <div class="round-card-header">
          <span class="round-card-title round-start">ROUND {{ currentRoundCard.round_number }}</span>
        </div>
        <div class="round-card-events" ref="currentEventsContainer">
          <div
            v-for="(evt, eIdx) in currentRoundCard.visibleEvents"
            :key="eIdx"
            class="fight-event"
            :class="{ 'critical-event': evt.isCritical }"
          >
            <span class="event-icon">{{ evt.emoji }}</span>
            <span class="event-text">{{ evt.text }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="fight-controls">
      <button v-if="!isFinished && !skipped" class="glass-button text-sm !py-2 !px-6 !rounded-full" @click="skipAnimation">
        ⏩ Pular para o resultado
      </button>
    </div>

    <!-- Final Result Card -->
    <div v-if="showFinalCard" class="final-result-card animate-fade-in">
      <div class="winner-title">{{ isDraw ? 'RESULTADO OFICIAL' : 'VENCEDOR' }}</div>
      <div class="winner-name-large">{{ isDraw ? 'EMPATE' : result.winner_name }}</div>
      <div class="result-method">
        Por {{ formatResultType(result.result_type) }}
        <span v-if="result.finish_round"> • Round {{ result.finish_round }}</span>
      </div>

      <div class="final-probabilities">
        <div class="final-prob-box">
          <h4>{{ fighter1?.name || result.fighter1_name || 'Lutador 1' }}</h4>
          <div class="prob-value">{{ Math.round(result.fighter1_probability || 0) }}%</div>
        </div>
        <div class="final-prob-box">
          <h4>{{ fighter2?.name || result.fighter2_name || 'Lutador 2' }}</h4>
          <div class="prob-value">{{ Math.round(result.fighter2_probability || 0) }}%</div>
        </div>
      </div>

      <div class="final-scoreboard">
        <div class="final-score-item">
          <span class="f1-color">{{ fighter1?.name || 'Lutador 1' }}</span>
          <span class="final-score-value">{{ f1TotalPoints }}</span>
        </div>
        <div class="final-score-vs">VS</div>
        <div class="final-score-item">
          <span class="f2-color">{{ fighter2?.name || 'Lutador 2' }}</span>
          <span class="final-score-value">{{ f2TotalPoints }}</span>
        </div>
      </div>

      <div class="final-actions">
        <button class="glass-button primary !py-3 !px-8 !rounded-full !font-bold" @click="$emit('simulateAgain')">
          🥊 SIMULAR NOVAMENTE
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import FighterNameDisplay from '@/components/events/FighterNameDisplay.vue'
import type { Fighter, SimulationResult } from '@/types'

const props = defineProps<{
  result: SimulationResult
  fighter1: Fighter | null
  fighter2: Fighter | null
}>()

const emit = defineEmits<{
  (e: 'simulateAgain'): void
}>()

interface RoundEvent {
  emoji: string
  text: string
  isCritical: boolean
}

interface CompletedRound {
  round_number: number
  f1_pts: number
  f2_pts: number
  events: RoundEvent[]
}

interface ActiveRound {
  round_number: number
  f1_pts: number
  f2_pts: number
  allEvents: RoundEvent[]
  visibleEvents: RoundEvent[]
}

const currentEventsContainer = ref<HTMLElement | null>(null)

const roundStatusText = ref('PREPARANDO')
const roundStatusClass = ref('')
const timeBarWidth = ref(0)
const timeBarTransition = ref('width 0.3s ease')
const completedRounds = ref<CompletedRound[]>([])
const currentRoundCard = ref<ActiveRound | null>(null)
const showFinalCard = ref(false)
const skipped = ref(false)
const isFinished = ref(false)

const f1Score = ref(0)
const f2Score = ref(0)
const f1TotalPoints = ref(0)
const f2TotalPoints = ref(0)

const momentum1 = computed(() => {
  const total = f1Score.value + f2Score.value
  return total > 0 ? (f1Score.value / total) * 100 : 50
})
const momentum2 = computed(() => {
  const total = f1Score.value + f2Score.value
  return total > 0 ? (f2Score.value / total) * 100 : 50
})

const isDraw = computed(() => {
  const rt = (props.result.result_type || '').toLowerCase()
  return rt.includes('draw') || rt.includes('empate')
})

function getRounds() {
  const details = props.result.simulation_details
  if (!details) return []
  if (Array.isArray(details)) return details
  if (details.rounds && Array.isArray(details.rounds)) return details.rounds
  return []
}

function getEventEmoji(text: string): string {
  const t = text.toLowerCase()
  if (t.includes('finalização') || t.includes('finalizacao') || t.includes('submission')) return '🔒'
  if (t.includes('knockdown') || t.includes('derrubou')) return '💥'
  if (t.includes('takedown') || t.includes('queda')) return '🤼'
  if (t.includes('dominou')) return '💪'
  if (t.includes('esquivou') || t.includes('defendeu')) return '🛡️'
  if (t.includes('avançou') || t.includes('combinacao')) return '👊'
  if (t.includes('uppercut') || t.includes('direto') || t.includes('certeiro')) return '🥊'
  if (t.includes('clinch') || t.includes('grade')) return '🤝'
  if (t.includes('centro') || t.includes('distancia')) return '👀'
  if (t.includes('chao') || t.includes('solo')) return '⬇️'
  return '🥊'
}

function isCriticalEvent(text: string): boolean {
  const t = text.toLowerCase()
  return (
    t.includes('finalização') || t.includes('finalizacao') ||
    t.includes('submission') || t.includes('knockdown') ||
    t.includes('derrubou') || t.includes('uppercut devastador') ||
    t.includes('certeiro')
  )
}

function toRoundEvents(rawEvents: string[]): RoundEvent[] {
  return (rawEvents || []).map((text) => ({
    emoji: getEventEmoji(text),
    text,
    isCritical: isCriticalEvent(text),
  }))
}

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

function formatResultType(type: string): string {
  const map: Record<string, string> = {
    KO: 'Nocaute (KO)',
    TKO: 'Nocaute Tecnico (TKO)',
    Submission: 'Finalizacao',
    Decision: 'Decisao',
  }
  return map[type] || type
}

function scrollToBottom() {
  nextTick(() => {
    currentEventsContainer.value?.scrollTo({
      top: currentEventsContainer.value.scrollHeight,
      behavior: 'smooth',
    })
  })
}

async function animateRound(round: any) {
  const roundNumber = round.round_number
  const f1_pts = round.fighter1_points || 0
  const f2_pts = round.fighter2_points || 0
  const allEvts = toRoundEvents(round.events)

  // Preparar card ativo
  currentRoundCard.value = {
    round_number: roundNumber,
    f1_pts,
    f2_pts,
    allEvents: allEvts,
    visibleEvents: [],
  }

  roundStatusText.value = `ROUND ${roundNumber}`
  roundStatusClass.value = 'round-start'
  await delay(2000)
  roundStatusClass.value = ''

  const roundDuration = 12000
  const eventDelay = allEvts.length > 0
    ? Math.max(roundDuration / (allEvts.length + 1), 1500)
    : roundDuration

  // Animar barra de tempo
  timeBarTransition.value = `width ${roundDuration}ms linear`
  await nextTick()
  timeBarWidth.value = 100

  // Mostrar eventos um por um
  for (let i = 0; i < allEvts.length; i++) {
    await delay(eventDelay)
    if (skipped.value) break
    currentRoundCard.value.visibleEvents.push(allEvts[i])
    scrollToBottom()
  }

  await delay(eventDelay)
  timeBarWidth.value = 0
  timeBarTransition.value = 'width 0.3s ease'

  if (skipped.value) return

  // Atualizar scores
  f1Score.value += f1_pts
  f2Score.value += f2_pts
  f1TotalPoints.value += Math.round(f1_pts)
  f2TotalPoints.value += Math.round(f2_pts)

  // Mover round para completados
  completedRounds.value.push({
    round_number: roundNumber,
    f1_pts,
    f2_pts,
    events: currentRoundCard.value.visibleEvents,
  })
  currentRoundCard.value = null

  await delay(500)
}

async function showRoundBreak() {
  roundStatusText.value = 'Intervalo entre rounds...'
  roundStatusClass.value = 'round-break'
  await delay(2000)
}

async function showFinalResult() {
  if (!skipped.value) await delay(800)
  showFinalCard.value = true
  isFinished.value = true
}

async function runAnimation() {
  const rounds = getRounds()
  if (rounds.length === 0) {
    showFinalResult()
    return
  }

  for (let i = 0; i < rounds.length; i++) {
    if (skipped.value) break
    await animateRound(rounds[i])
    if (skipped.value) break
    if (i < rounds.length - 1) {
      await showRoundBreak()
    }
  }

  await showFinalResult()
}

function skipAnimation() {
  skipped.value = true
  // Mover round ativo para completado
  if (currentRoundCard.value) {
    completedRounds.value.push({
      round_number: currentRoundCard.value.round_number,
      f1_pts: currentRoundCard.value.f1_pts,
      f2_pts: currentRoundCard.value.f2_pts,
      events: currentRoundCard.value.allEvents,
    })
    currentRoundCard.value = null
  }
  showFinalResult()
}

onMounted(() => {
  runAnimation()
})
</script>

<style scoped>
.fight-live-animation {
  padding: 1.5rem;
  max-width: 800px;
  margin: 0 auto;
  overflow: hidden;
}

.fight-header {
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.fighter-corner {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 12px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid transparent;
  transition: all 0.3s ease;
}

.fighter-corner.winner {
  border-color: rgba(234, 179, 8, 0.3);
  background: rgba(234, 179, 8, 0.05);
}

.corner-label {
  font-size: 0.6rem;
  font-weight: 800;
  letter-spacing: 2px;
  text-transform: uppercase;
  margin-bottom: 6px;
  padding: 2px 8px;
  border-radius: 4px;
}

.red-corner {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.blue-corner {
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.1);
}

.fighter-photo {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  overflow: hidden;
  margin-bottom: 10px;
  background: rgba(255, 255, 255, 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--glass-border);
}

.fighter-photo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-fallback {
  font-size: 2rem;
}

.corner-name {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
  line-height: 1.3;
}

.momentum-bar {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 10px;
}

.momentum-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--accent));
  border-radius: 3px;
  transition: width 0.5s ease;
}

.corner-stats {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
}

.stat-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.stat-box small {
  font-size: 0.6rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-box span {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
}

.probability-badge {
  font-size: 0.75rem;
  color: var(--primary);
  font-weight: 700;
  margin-top: 4px;
}

.prob-right {
  color: var(--accent);
}

.fight-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-width: 120px;
  padding: 8px 0;
}

.round-indicator {
  font-size: 0.9rem;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: 2px;
  text-align: center;
  padding: 6px 14px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.round-indicator.round-start {
  background: rgba(124, 58, 237, 0.2);
  color: var(--accent-light);
  animation: pulse 1s ease-in-out infinite;
}

.round-indicator.round-break {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-muted);
  font-size: 0.75rem;
}

.time-bar-container {
  width: 100%;
  height: 4px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 2px;
  overflow: hidden;
}

.time-bar {
  height: 100%;
  background: linear-gradient(90deg, #ef4444, #eab308, #22c55e);
  border-radius: 2px;
  width: 0%;
}

.live-badge {
  font-size: 0.65rem;
  font-weight: 800;
  color: #ef4444;
  letter-spacing: 2px;
  animation: pulse 2s ease-in-out infinite;
}

.round-cards-area {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 12px;
}

.round-card {
  border-radius: 12px;
  overflow: hidden;
  animation: fadeInUp 0.4s ease forwards;
}

.round-card.completed {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.round-card.active {
  background: rgba(124, 58, 237, 0.06);
  border: 1px solid rgba(124, 58, 237, 0.15);
}

.round-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.round-card-title {
  font-size: 0.8rem;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: 1.5px;
}

.round-card-title.round-start {
  animation: pulse 1s ease-in-out infinite;
  color: var(--accent-light);
}

.round-card-score {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-secondary);
}

.round-card-events {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 10px;
  max-height: 250px;
  overflow-y: auto;
}

.fight-event {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.03);
  font-size: 0.82rem;
  color: var(--text-secondary);
  animation: fadeInUp 0.3s ease forwards;
}

.fight-event.critical-event {
  background: rgba(239, 68, 68, 0.1);
  border-left: 3px solid #ef4444;
}

.event-icon {
  font-size: 1rem;
  flex-shrink: 0;
}

.event-text {
  line-height: 1.4;
}

.fight-controls {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.final-result-card {
  text-align: center;
  padding: 2rem;
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(0, 0, 0, 0.2));
  border: 1px solid rgba(124, 58, 237, 0.2);
  margin-top: 16px;
}

.winner-title {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 3px;
  margin-bottom: 8px;
}

.winner-name-large {
  font-size: 2rem;
  font-weight: 900;
  color: #eab308;
  margin-bottom: 8px;
}

.result-method {
  font-size: 1rem;
  color: var(--text-secondary);
  font-weight: 600;
  margin-bottom: 24px;
}

.final-probabilities {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.final-prob-box {
  padding: 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
}

.final-prob-box h4 {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-bottom: 6px;
  text-transform: uppercase;
}

.final-prob-box .prob-value {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--text-primary);
}

.final-scoreboard {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 24px;
  padding: 12px 0;
}

.final-score-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font-size: 0.8rem;
  font-weight: 600;
}

.final-score-value {
  font-size: 1.3rem;
  font-weight: 800;
  color: var(--text-primary);
}

.final-score-vs {
  font-size: 0.75rem;
  font-weight: 800;
  color: var(--text-muted);
  letter-spacing: 2px;
}

.final-actions {
  display: flex;
  justify-content: center;
}

.f1-color {
  color: var(--primary);
}

.f2-color {
  color: var(--accent);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 640px) {
  .fight-header {
    flex-direction: column;
    gap: 12px;
  }
  .fighter-photo {
    width: 60px;
    height: 60px;
  }
  .final-probabilities {
    grid-template-columns: 1fr;
  }
}
</style>
