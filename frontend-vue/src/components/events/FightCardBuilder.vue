<template>
  <div class="fight-card-builder">
    <div
      v-for="(fight, index) in fights"
      :key="index"
      class="fight-slot glass-card"
      :class="{ 'title-fight': fight.is_title_fight }"
    >
      <div class="slot-header">
        <div class="slot-title">
          <span class="slot-number">{{ getFightLabel(index) }}</span>
          <span v-if="fight.is_title_fight" class="title-badge">🏆 TITLE</span>
        </div>
        <button class="remove-btn" @click="removeFight(index)" :title="t('events.removeFight')">
          ✕
        </button>
      </div>

      <div class="slot-body">
        <!-- Red Corner -->
        <div class="fighter-side red-side">
          <div class="corner-badge red">🟥 RED CORNER</div>
          <FighterSelector
            v-model="fight.fighter1"
            :placeholder="'Buscar Lutador 1'"
          />
        </div>

        <!-- VS -->
        <div class="vs-divider">
          <span class="vs-text">VS</span>
        </div>

        <!-- Blue Corner -->
        <div class="fighter-side blue-side">
          <div class="corner-badge blue">🟦 BLUE CORNER</div>
          <FighterSelector
            v-model="fight.fighter2"
            :placeholder="'Buscar Lutador 2'"
          />
        </div>
      </div>

      <div class="slot-footer">
        <div class="footer-grid">
          <div class="field">
            <label>{{ t('events.position') }}</label>
            <Select
              v-model="fight.fight_type"
              :options="positionOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('events.position')"
              class="w-full"
            />
          </div>
          <div class="field">
            <label>Categoria</label>
            <Select
              v-model="fight.weight_class"
              :options="weightClassOptions"
              option-label="label"
              option-value="value"
              placeholder="Categoria"
              class="w-full"
            />
          </div>
          <div class="field">
            <label>Rounds</label>
            <Select
              v-model="fight.rounds"
              :options="roundOptions"
              option-label="label"
              option-value="value"
              placeholder="Rounds"
              class="w-full"
            />
          </div>
          <div class="field checkbox-field">
            <label class="checkbox-label">
              <input v-model="fight.is_title_fight" type="checkbox" class="checkbox-input" />
              <span class="checkbox-text">🏆 Luta de Título</span>
            </label>
          </div>
        </div>
      </div>
    </div>

    <button class="add-fight-btn glass-card" @click="addFight">
      + {{ t('events.addFight') }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Select from 'primevue/select'
import FighterSelector from '@/components/ui/FighterSelector.vue'
import { api } from '@/services/api'
import type { Fighter, FightCreate } from '@/types'

const { t } = useI18n()

interface FightSlot {
  fighter1: Fighter | null
  fighter2: Fighter | null
  fight_type: string
  weight_class: string | undefined
  rounds: number
  is_title_fight: boolean
  fight_order: number
  fighter1_id?: string
  fighter2_id?: string
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

const weightClassOptions = [
  { label: 'Flyweight', value: 'Flyweight' },
  { label: 'Bantamweight', value: 'Bantamweight' },
  { label: 'Featherweight', value: 'Featherweight' },
  { label: 'Lightweight', value: 'Lightweight' },
  { label: 'Welterweight', value: 'Welterweight' },
  { label: 'Middleweight', value: 'Middleweight' },
  { label: 'Light Heavyweight', value: 'Light Heavyweight' },
  { label: 'Heavyweight', value: 'Heavyweight' },
]

const roundOptions = [
  { label: '3 Rounds', value: 3 },
  { label: '5 Rounds', value: 5 },
]

const fights = ref<FightSlot[]>([])

watch(
  () => props.modelValue,
  async (val) => {
    if (val.length === 0 && fights.value.length === 0) {
      fights.value = []
    } else if (val.length > 0) {
      const slots: FightSlot[] = val.map((f, i) => ({
        fighter1: null as Fighter | null,
        fighter2: null as Fighter | null,
        fight_type: f.fight_type || 'main_card',
        weight_class: f.weight_class || undefined,
        rounds: f.rounds || 3,
        is_title_fight: f.is_title_fight || false,
        fight_order: f.fight_order || i + 1,
        fighter1_id: f.fighter1_id,
        fighter2_id: f.fighter2_id,
      }))

      // Fetch fighter details for existing fights
      const idsToFetch = new Set<string>()
      slots.forEach((s) => {
        if (s.fighter1_id) idsToFetch.add(s.fighter1_id)
        if (s.fighter2_id) idsToFetch.add(s.fighter2_id)
      })

      if (idsToFetch.size > 0) {
        try {
          const results = await Promise.all(
            Array.from(idsToFetch).map((id) => api.getFighter(id).catch(() => null))
          )
          const map: Record<string, Fighter> = {}
          results.filter(Boolean).forEach((f) => {
            if (f) map[String(f.id)] = f as Fighter
          })

          slots.forEach((s) => {
            if (s.fighter1_id && map[s.fighter1_id]) {
              s.fighter1 = map[s.fighter1_id]
            }
            if (s.fighter2_id && map[s.fighter2_id]) {
              s.fighter2 = map[s.fighter2_id]
            }
          })
        } catch {
          // silently ignore
        }
      }

      fights.value = slots
    }
  },
  { immediate: true },
)

function getFightLabel(index: number): string {
  const total = fights.value.length
  const order = total - index // Main Event = maior número
  if (order === 1) return 'Main Event'
  if (order === 2) return 'Co-Main Event'
  return `Luta ${order}`
}

function syncToModel() {
  const result: FightCreate[] = fights.value
    .filter((f) => f.fighter1 && f.fighter2)
    .map((f, i) => ({
      fighter1_id: f.fighter1!.id,
      fighter2_id: f.fighter2!.id,
      fight_type: f.fight_type,
      weight_class: f.weight_class,
      rounds: f.rounds,
      is_title_fight: f.is_title_fight,
      fight_order: fights.value.length - i, // Main event = 1
    }))
  emit('update:modelValue', result)
}

watch(fights, syncToModel, { deep: true })

function addFight() {
  fights.value.unshift({
    fighter1: null,
    fighter2: null,
    fight_type: 'main_card',
    weight_class: undefined,
    rounds: 3,
    is_title_fight: false,
    fight_order: 1,
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
  transition: all 0.3s ease;
  border: 1px solid var(--glass-border);
}

.fight-slot.title-fight {
  border-color: rgba(234, 179, 8, 0.3);
  box-shadow: 0 0 20px rgba(234, 179, 8, 0.05);
}

.slot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--glass-border);
}

.slot-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.slot-number {
  font-weight: 800;
  color: var(--text-primary);
  font-size: 0.95rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.title-badge {
  padding: 2px 10px;
  border-radius: 8px;
  font-size: 0.7rem;
  font-weight: 700;
  background: rgba(234, 179, 8, 0.15);
  color: #eab308;
  text-transform: uppercase;
  letter-spacing: 0.5px;
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
  grid-template-columns: 1fr auto 1fr;
  gap: 12px;
  align-items: start;
  margin-bottom: 16px;
}

.fighter-side {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.red-side {
  padding: 10px;
  border-radius: 12px;
  background: rgba(239, 68, 68, 0.04);
  border: 1px solid rgba(239, 68, 68, 0.1);
}

.blue-side {
  padding: 10px;
  border-radius: 12px;
  background: rgba(59, 130, 246, 0.04);
  border: 1px solid rgba(59, 130, 246, 0.1);
}

.corner-badge {
  font-size: 0.7rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 1px;
  text-align: center;
  padding: 4px 8px;
  border-radius: 6px;
}

.corner-badge.red {
  color: #f87171;
  background: rgba(239, 68, 68, 0.1);
}

.corner-badge.blue {
  color: #60a5fa;
  background: rgba(59, 130, 246, 0.1);
}

.vs-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  padding-top: 24px;
}

.vs-text {
  font-size: 0.9rem;
  font-weight: 900;
  color: var(--text-muted);
  letter-spacing: 2px;
}

.slot-footer {
  padding-top: 12px;
  border-top: 1px solid var(--glass-border);
}

.footer-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

@media (min-width: 768px) {
  .footer-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.checkbox-field {
  display: flex;
  align-items: flex-end;
  padding-bottom: 2px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--glass-border);
  transition: all 0.3s ease;
}

.checkbox-label:hover {
  background: rgba(255, 255, 255, 0.06);
}

.checkbox-input {
  width: 16px;
  height: 16px;
  accent-color: var(--accent);
  cursor: pointer;
}

.checkbox-text {
  font-size: 0.85rem;
  color: var(--text-primary);
  font-weight: 600;
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

@media (max-width: 768px) {
  .slot-body {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  .vs-divider {
    padding-top: 0;
    order: -1;
  }
}
</style>
