<template>
  <div class="attribute-bar">
    <div class="attr-header">
      <span class="attr-label">{{ label }}</span>
      <span class="attr-value" :style="{ color: barColor }">{{ value }}</span>
    </div>
    <div class="bar-track">
      <div
        class="bar-fill"
        :style="{ width: `${value}%`, backgroundColor: barColor }"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    label: string
    value: number
    color?: string
  }>(),
  {
    color: 'var(--accent)',
  },
)

const barColor = computed(() => {
  if (props.value >= 90) return 'var(--gold)'
  if (props.value >= 80) return 'var(--primary)'
  if (props.value >= 65) return props.color
  return 'var(--text-muted)'
})
</script>

<style scoped>
.attribute-bar {
  margin-bottom: 12px;
}

.attr-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.attr-label {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  font-weight: 500;
  text-transform: capitalize;
}

.attr-value {
  font-size: 0.875rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.bar-track {
  height: 6px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 3px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 0;
}
</style>
