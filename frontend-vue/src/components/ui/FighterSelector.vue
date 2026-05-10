<template>
  <div class="fighter-selector">
    <label v-if="label" class="selector-label">{{ label }}</label>
    <AutoComplete
      v-model="selectedFighter"
      :suggestions="suggestions"
      :placeholder="placeholder"
      :delay="300"
      field="name"
      optionLabel="name"
      :inputStyle="{ width: '100%' }"
      @complete="searchFighters"
      @clear="clearSelection"
      class="w-full"
      dropdown
      emptySearchMessage="Nenhum lutador encontrado"
    >
      <template #option="slotProps">
        <div class="option-item">
          <div class="option-name">
            {{ slotProps.option.name }}
            <span v-if="slotProps.option.nickname" class="option-nickname">
              "{{ slotProps.option.nickname }}"
            </span>
          </div>
          <div class="option-meta">
            <span v-if="slotProps.option.last_organization_fight" class="option-org">
              {{ slotProps.option.last_organization_fight }}
            </span>
            <span v-if="slotProps.option.actual_weight_class" class="option-weight">
              {{ slotProps.option.actual_weight_class }}
            </span>
            <span class="option-overall" :style="{ color: getOverallColor(slotProps.option.overall_rating) }">
              {{ slotProps.option.overall_rating }}
            </span>
          </div>
        </div>
      </template>
    </AutoComplete>

    <div v-if="modelValue" class="selected-fighter glass-card">
      <div class="selected-name">{{ modelValue.name }}</div>
      <div class="selected-meta">
        <span v-if="modelValue.last_organization_fight">{{ modelValue.last_organization_fight }}</span>
        <span v-if="modelValue.actual_weight_class">{{ modelValue.actual_weight_class }}</span>
        <span class="overall-badge" :style="{ backgroundColor: getOverallColor(modelValue.overall_rating) }">
          {{ modelValue.overall_rating }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import AutoComplete from 'primevue/autocomplete'
import { api } from '@/services/api'
import type { Fighter } from '@/types'

const props = defineProps<{
  modelValue: Fighter | null
  placeholder?: string
  label?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: Fighter | null]
}>()

const selectedFighter = ref<Fighter | null>(props.modelValue)
const suggestions = ref<Fighter[]>([])

watch(
  () => props.modelValue,
  (val) => {
    selectedFighter.value = val
  },
)

watch(selectedFighter, (val) => {
  emit('update:modelValue', val)
})

async function searchFighters(event: { query: string }) {
  if (!event.query || event.query.length < 2) {
    suggestions.value = []
    return
  }
  try {
    const result = await api.getFighters({ name: event.query, limit: 10 })
    suggestions.value = result.fighters || []
  } catch {
    suggestions.value = []
  }
}

function clearSelection() {
  selectedFighter.value = null
}

function getOverallColor(overall: number): string {
  if (overall >= 90) return 'var(--gold)'
  if (overall >= 80) return 'var(--primary)'
  if (overall >= 65) return 'var(--accent)'
  return 'var(--text-muted)'
}
</script>

<style scoped>
.fighter-selector {
  width: 100%;
}

.selector-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.w-full {
  width: 100%;
}

.option-item {
  padding: 2px 0;
}

.option-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.9rem;
}

.option-nickname {
  color: var(--text-muted);
  font-weight: 400;
  font-style: italic;
}

.option-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 2px;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.option-org {
  background: rgba(124, 58, 237, 0.15);
  color: var(--accent-light);
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.option-overall {
  font-weight: 700;
}

.selected-fighter {
  margin-top: 12px;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.selected-name {
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--text-primary);
}

.selected-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.overall-badge {
  color: #fff;
  padding: 2px 10px;
  border-radius: 12px;
  font-weight: 700;
  font-size: 0.85rem;
}
</style>
