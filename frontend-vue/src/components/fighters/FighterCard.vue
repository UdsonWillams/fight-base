<template>
  <div
    class="fighter-card glass-card hoverable"
    :class="{ clickable }"
    @click="handleClick"
  >
    <div class="card-header">
      <h3 class="fighter-name">{{ fighter.name }}</h3>
      <div class="overall-badge" :style="{ backgroundColor: getOverallColor(fighter.overall_rating) }">
        {{ fighter.overall_rating }}
      </div>
    </div>

    <p v-if="fighter.nickname" class="fighter-nickname">"{{ fighter.nickname }}"</p>

    <div class="card-meta">
      <span v-if="fighter.last_organization_fight" class="meta-tag org-tag">
        {{ fighter.last_organization_fight }}
      </span>
      <span v-if="fighter.actual_weight_class" class="meta-tag">
        {{ fighter.actual_weight_class }}
      </span>
      <span v-if="fighter.fighting_style" class="meta-tag style-tag">
        {{ fighter.fighting_style }}
      </span>
    </div>

    <div class="record-section">
      <span class="record-label">Cartel</span>
      <span class="record-value">
        <span class="wins">{{ fighter.wins }}</span>
        -
        <span class="losses">{{ fighter.losses }}</span>
        -
        <span class="draws">{{ fighter.draws }}</span>
      </span>
    </div>

    <div class="mini-attributes">
      <div class="mini-bar">
        <span class="mini-label">STR</span>
        <div class="mini-track">
          <div class="mini-fill" :style="{ width: `${fighter.striking}%`, backgroundColor: getBarColor(fighter.striking) }" />
        </div>
      </div>
      <div class="mini-bar">
        <span class="mini-label">GRP</span>
        <div class="mini-track">
          <div class="mini-fill" :style="{ width: `${fighter.grappling}%`, backgroundColor: getBarColor(fighter.grappling) }" />
        </div>
      </div>
      <div class="mini-bar">
        <span class="mini-label">DEF</span>
        <div class="mini-track">
          <div class="mini-fill" :style="{ width: `${fighter.defense}%`, backgroundColor: getBarColor(fighter.defense) }" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Fighter } from '@/types'

const props = defineProps<{
  fighter: Fighter
  clickable?: boolean
}>()

const emit = defineEmits<{
  click: [fighter: Fighter]
}>()

function handleClick() {
  emit('click', props.fighter)
}

function getOverallColor(overall: number): string {
  if (overall >= 90) return 'var(--gold)'
  if (overall >= 80) return 'var(--primary)'
  if (overall >= 65) return 'var(--accent)'
  return 'var(--text-muted)'
}

function getBarColor(value: number): string {
  if (value >= 90) return 'var(--gold)'
  if (value >= 80) return 'var(--primary)'
  if (value >= 65) return 'var(--accent)'
  return 'var(--text-muted)'
}
</script>

<style scoped>
.fighter-card {
  padding: 1.25rem;
  cursor: default;
}

.fighter-card.clickable {
  cursor: pointer;
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 4px;
}

.fighter-name {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.3;
}

.overall-badge {
  color: #fff;
  padding: 3px 10px;
  border-radius: 12px;
  font-weight: 800;
  font-size: 0.95rem;
  flex-shrink: 0;
}

.fighter-nickname {
  color: var(--text-muted);
  font-style: italic;
  font-size: 0.8125rem;
  margin-bottom: 10px;
}

.card-meta {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.meta-tag {
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-secondary);
}

.org-tag {
  background: rgba(124, 58, 237, 0.12);
  color: var(--accent-light);
}

.style-tag {
  background: rgba(59, 130, 246, 0.12);
  color: var(--primary-light);
}

.record-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--glass-border);
}

.record-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.record-value {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
}

.wins { color: var(--success); }
.losses { color: var(--danger); }
.draws { color: var(--text-secondary); }

.mini-attributes {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.mini-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mini-label {
  font-size: 0.65rem;
  font-weight: 700;
  color: var(--text-muted);
  width: 24px;
  text-align: right;
}

.mini-track {
  flex: 1;
  height: 4px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 2px;
  overflow: hidden;
}

.mini-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.4s ease;
}
</style>
