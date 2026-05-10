<template>
  <div class="fight-card-builder">
    <div v-for="(fight, index) in fights" :key="index" class="fight-slot glass-card">
      <div class="slot-header">
        <span class="slot-number">Luta {{ index + 1 }}</span>
        <button class="remove-btn" @click="removeFight(index)" :title="t('event.removeFight')">
          &#x2715;
        </button>
      </div>

      <div class="slot-body">
        <div class="fighter-select">
          <label>Lutador 1</label>
          <FighterSelector
            v-model="fight.fighter1"
            :placeholder="'Buscar Lutador 1'"
          />
        </div>
        <div class="fighter-select">
          <label>Lutador 2</label>
          <FighterSelector
            v-model="fight.fighter2"
            :placeholder="'Buscar Lutador 2'"
          />
        </div>
      </div>

      <div class="slot-footer">
        <div class="field">
          <label>{{ t('event.position') }}</label>
          <Select
            v-model="fight.fight_type"
            :options="positionOptions"
            optionLabel="label"
            optionValue="value"
            :placeholder="t('event.position')"
          />
        </div>
      </div>
    </div>

    <button class="add-fight-btn glass-card" @click="addFight">
      + {{ t('event.addFight') }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Select from 'primevue/select'
import FighterSelector from '@/components/ui/FighterSelector.vue'
import type { Fighter, FightCreate } from '@/types'

const { t } = useI18n()

interface FightSlot {
  fighter1: Fighter | null
  fighter2: Fighter | null
  fight_type: string
}

const props = defineProps<{
  modelValue: FightCreate[]
  eventId: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: FightCreate[]]
}>()

const positionOptions = [
  { label: 'Main Event', value: 'main' },
  { label: 'Co-Main', value: 'co-main' },
  { label: 'Main Card', value: 'main_card' },
  { label: 'Preliminar', value: 'preliminary' },
]

const fights = ref<FightSlot[]>([])

watch(
  () => props.modelValue,
  (val) => {
    fights.value = val.map((f) => ({
      fighter1: null as Fighter | null,
      fighter2: null as Fighter | null,
      fight_type: f.fight_type || 'main_card',
    }))
  },
  { immediate: true },
)

function syncToModel() {
  const result: FightCreate[] = fights.value
    .filter((f) => f.fighter1 && f.fighter2)
    .map((f, i) => ({
      fighter1_id: f.fighter1!.id,
      fighter2_id: f.fighter2!.id,
      fight_type: f.fight_type,
      fight_order: i + 1,
    }))
  emit('update:modelValue', result)
}

watch(fights, syncToModel, { deep: true })

function addFight() {
  fights.value.push({
    fighter1: null,
    fighter2: null,
    fight_type: 'main_card',
  })
}

function removeFight(index: number) {
  fights.value.splice(index, 1)
}
</script>

<style scoped>
.fight-card-builder {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.fight-slot {
  padding: 1.25rem;
}

.slot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.slot-number {
  font-weight: 700;
  color: var(--text-primary);
  font-size: 0.9rem;
}

.remove-btn {
  background: none;
  border: none;
  color: var(--danger);
  cursor: pointer;
  font-size: 1rem;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all var(--transition);
}

.remove-btn:hover {
  background: rgba(239, 68, 68, 0.1);
}

.slot-body {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-bottom: 14px;
}

.fighter-select label {
  display: block;
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 4px;
}

.slot-footer {
  padding-top: 10px;
  border-top: 1px solid var(--glass-border);
}

.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 200px;
}

.field label {
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.add-fight-btn {
  padding: 14px;
  text-align: center;
  background: transparent;
  border: 1px dashed var(--glass-border);
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition);
  border-radius: var(--radius-lg);
}

.add-fight-btn:hover {
  border-color: var(--accent);
  color: var(--accent-light);
  background: rgba(124, 58, 237, 0.05);
}
</style>
