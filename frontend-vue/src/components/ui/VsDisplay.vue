<template>
  <div class="vs-display">
    <div class="fighter-side glass-card">
      <div v-if="fighter1" class="fighter-info">
        <h3 class="fighter-name">
          <span v-if="fighter1.nickname && fighter1.name">
            <template v-for="(part, i) in formatNameWithNickname(fighter1.name, fighter1.nickname)" :key="i">
              <span v-if="part.type === 'nickname'" class="fighter-nickname-inline">"{{ part.text }}"</span>
              <span v-else>{{ part.text }}</span>
            </template>
          </span>
          <span v-else>{{ fighter1.name }}</span>
        </h3>
        <div class="fighter-meta">
          <span v-if="fighter1.last_organization_fight" class="meta-badge org-badge">
            {{ fighter1.last_organization_fight }}
          </span>
          <span v-if="fighter1.actual_weight_class" class="meta-badge">
            {{ fighter1.actual_weight_class }}
          </span>
        </div>
        <div class="overall-row">
          <span class="overall-number" :style="{ color: getOverallColor(fighter1.overall_rating) }">
            {{ fighter1.overall_rating }}
          </span>
          <span class="overall-label">Overall</span>
        </div>
        <div v-if="fighter1.record" class="record-row">
          <span class="record-text">{{ fighter1.record }}</span>
        </div>
        <div v-else class="record-row">
          <span class="record-text">{{ fighter1.wins }}-{{ fighter1.losses }}-{{ fighter1.draws }}</span>
        </div>
      </div>
      <div v-else class="fighter-empty">
        <span class="empty-text">Selecionar Lutador</span>
      </div>
    </div>

    <div class="vs-center">
      <span class="vs-text">VS</span>
    </div>

    <div class="fighter-side glass-card">
      <div v-if="fighter2" class="fighter-info">
        <h3 class="fighter-name">
          <span v-if="fighter2.nickname && fighter2.name">
            <template v-for="(part, i) in formatNameWithNickname(fighter2.name, fighter2.nickname)" :key="i">
              <span v-if="part.type === 'nickname'" class="fighter-nickname-inline">"{{ part.text }}"</span>
              <span v-else>{{ part.text }}</span>
            </template>
          </span>
          <span v-else>{{ fighter2.name }}</span>
        </h3>
        <div class="fighter-meta">
          <span v-if="fighter2.last_organization_fight" class="meta-badge org-badge">
            {{ fighter2.last_organization_fight }}
          </span>
          <span v-if="fighter2.actual_weight_class" class="meta-badge">
            {{ fighter2.actual_weight_class }}
          </span>
        </div>
        <div class="overall-row">
          <span class="overall-number" :style="{ color: getOverallColor(fighter2.overall_rating) }">
            {{ fighter2.overall_rating }}
          </span>
          <span class="overall-label">Overall</span>
        </div>
        <div v-if="fighter2.record" class="record-row">
          <span class="record-text">{{ fighter2.record }}</span>
        </div>
        <div v-else class="record-row">
          <span class="record-text">{{ fighter2.wins }}-{{ fighter2.losses }}-{{ fighter2.draws }}</span>
        </div>
      </div>
      <div v-else class="fighter-empty">
        <span class="empty-text">Selecionar Lutador</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Fighter } from '@/types'

defineProps<{
  fighter1: Fighter | null
  fighter2: Fighter | null
}>()

function getOverallColor(overall: number): string {
  if (overall >= 90) return 'var(--gold)'
  if (overall >= 80) return 'var(--primary)'
  if (overall >= 65) return 'var(--accent)'
  return 'var(--text-muted)'
}

function formatNameWithNickname(name: string, nickname: string) {
  const parts = name.trim().split(' ')
  if (parts.length >= 2) {
    const firstName = parts[0]
    const lastNames = parts.slice(1).join(' ')
    return [
      { text: firstName + ' ', type: 'name' },
      { text: nickname, type: 'nickname' },
      { text: ' ' + lastNames, type: 'name' },
    ]
  }
  return [
    { text: name + ' ', type: 'name' },
    { text: nickname, type: 'nickname' },
  ]
}
</script>

<style scoped>
.vs-display {
  display: flex;
  align-items: stretch;
  justify-content: center;
  gap: 0;
  width: 100%;
}

.fighter-side {
  flex: 1;
  max-width: 360px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fighter-side:first-child {
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
  border-right: none;
}

.fighter-side:last-child {
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
  border-left: none;
}

.fighter-info {
  text-align: center;
}

.fighter-name {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 6px;
  line-height: 1.3;
}

.fighter-nickname-inline {
  color: var(--accent-light);
  font-style: italic;
  font-weight: 500;
  font-size: 0.95rem;
}

.fighter-nickname {
  color: var(--text-muted);
  font-style: italic;
  font-size: 0.85rem;
  margin-bottom: 8px;
}

.fighter-meta {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.meta-badge {
  padding: 3px 12px;
  border-radius: 12px;
  font-size: 0.75rem;
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-secondary);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.org-badge {
  background: rgba(124, 58, 237, 0.15);
  color: var(--accent-light);
}

.overall-row {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 6px;
  margin-bottom: 6px;
}

.overall-number {
  font-size: 2.5rem;
  font-weight: 800;
  text-shadow: 0 0 20px rgba(168, 85, 247, 0.3);
}

.overall-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.record-row {
  margin-top: 4px;
}

.record-text {
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.fighter-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 0;
}

.empty-text {
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-style: italic;
}

.vs-center {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 20px;
  flex-shrink: 0;
  z-index: 1;
}

.vs-text {
  font-size: 2rem;
  font-weight: 900;
  color: var(--text-secondary);
  animation: pulse 2s ease-in-out infinite;
}

@media (max-width: 640px) {
  .vs-display {
    flex-direction: column;
    gap: 0;
  }

  .fighter-side {
    max-width: 100%;
  }

  .fighter-side:first-child {
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    border-right: 1px solid var(--glass-border);
    border-bottom: none;
  }

  .fighter-side:last-child {
    border-radius: 0 0 var(--radius-lg) var(--radius-lg);
    border-left: 1px solid var(--glass-border);
    border-top: none;
  }

  .vs-center {
    padding: 12px 0;
  }
}
</style>
