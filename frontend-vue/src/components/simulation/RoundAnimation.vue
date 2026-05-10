<template>
  <div class="round-animation">
    <div v-if="roundDetails.length === 0" class="no-rounds">
      <span>{{ t('simulation.noHistory') }}</span>
    </div>

    <div class="rounds-progress">
      <div
        v-for="(round, rIndex) in roundDetails"
        :key="rIndex"
        class="round-indicator"
        :class="{ active: rIndex <= currentRound, current: rIndex === currentRound }"
        @click="currentRound = rIndex"
      >
        R{{ round.round_number }}
      </div>
    </div>

    <div class="round-content">
      <TransitionGroup name="event-list">
        <div
          v-for="(round, rIndex) in visibleRounds"
          :key="rIndex"
          class="round-section"
        >
          <h4 class="round-title">{{ t('simulation.roundNumber', { number: round.round_number }) }}</h4>
          <TransitionGroup name="event-item" tag="ul" class="events-list">
            <li
              v-for="(event, eIndex) in round.events"
              :key="`${rIndex}-${eIndex}`"
              class="event-item"
              :style="{ animationDelay: `${eIndex * 0.1}s` }"
            >
              <span class="event-dot" />
              <span class="event-text">{{ event }}</span>
            </li>
          </TransitionGroup>
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { RoundDetail } from '@/types'

const { t } = useI18n()

const props = withDefaults(
  defineProps<{
    roundDetails: RoundDetail[]
  }>(),
  {
    roundDetails: () => [],
  },
)

const currentRound = ref(0)

watch(
  () => props.roundDetails,
  (details) => {
    if (details.length > 0) {
      currentRound.value = details.length - 1
    }
  },
  { immediate: true },
)

const visibleRounds = computed(() => {
  return props.roundDetails.slice(0, currentRound.value + 1)
})
</script>

<style scoped>
.round-animation {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.no-rounds {
  text-align: center;
  padding: 2rem;
  color: var(--text-muted);
}

.rounds-progress {
  display: flex;
  gap: 6px;
  justify-content: center;
  flex-wrap: wrap;
}

.round-indicator {
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--glass-border);
  cursor: pointer;
  transition: all var(--transition);
}

.round-indicator.active {
  color: var(--text-primary);
  background: rgba(124, 58, 237, 0.15);
  border-color: var(--accent);
}

.round-indicator.current {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
}

.round-content {
  min-height: 100px;
}

.round-section {
  margin-bottom: 16px;
}

.round-title {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--glass-border);
}

.events-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.event-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 0.85rem;
  color: var(--text-secondary);
  animation: fadeInUp 0.4s ease forwards;
  opacity: 0;
}

.event-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  margin-top: 6px;
  flex-shrink: 0;
}

.event-text {
  line-height: 1.5;
}

.event-list-enter-active,
.event-list-leave-active {
  transition: all 0.4s ease;
}

.event-list-enter-from,
.event-list-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
