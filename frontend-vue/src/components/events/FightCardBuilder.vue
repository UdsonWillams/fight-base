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
        <div class="slot-header-right">
          <span v-if="fight.existingResult" class="result-badge-compact" :class="'result-' + (fight.existingResult || '').toLowerCase()">
            {{ fight.existingResult }}
            <template v-if="fight.existingWinner"> — {{ fight.existingWinner }}</template>
            <template v-if="fight.existingRound"> R{{ fight.existingRound }}</template>
          </span>
          <button class="remove-btn" @click="removeFight(index)" :title="t('events.removeFight')">
            ✕
          </button>
        </div>
      </div>

      <div class="slot-body">
        <div class="fighter-side red-side">
          <div class="corner-badge red">🟥 RED CORNER</div>
          <FighterSelector
            v-model="fight.fighter1"
            :placeholder="'Buscar Lutador 1'"
          />
        </div>
        <div class="vs-divider">
          <span class="vs-text">VS</span>
        </div>
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

      <div v-if="eventStatus === 'in_progress' || eventStatus === 'completed'" class="result-section">
        <button
          class="result-toggle-btn"
          @click="fight.showResult = !fight.showResult"
        >
          <span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="inline-block mr-1">
              <path d="M12 20h9" /><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
            </svg>
            {{ fight.showResult ? 'Fechar Resultado' : 'Editar Resultado' }}
          </span>
          <svg
            width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
            class="transition-transform"
            :class="{ 'rotate-180': fight.showResult }"
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>

        <div v-if="fight.showResult" class="result-form">
          <div class="field">
            <label>Vencedor</label>
            <div class="winner-options">
              <label class="winner-option" :class="{ active: fight.resultWinner === 'fighter1' }">
                <input v-model="fight.resultWinner" type="radio" value="fighter1" class="sr-only" />
                <span class="label-text">{{ fight.fighter1?.name || 'Lutador 1' }}</span>
              </label>
              <label class="winner-option" :class="{ active: fight.resultWinner === 'fighter2' }">
                <input v-model="fight.resultWinner" type="radio" value="fighter2" class="sr-only" />
                <span class="label-text">{{ fight.fighter2?.name || 'Lutador 2' }}</span>
              </label>
              <label class="winner-option draw-option" :class="{ active: fight.resultWinner === 'draw' }">
                <input v-model="fight.resultWinner" type="radio" value="draw" class="sr-only" />
                <span class="label-text">Empate</span>
              </label>
              <label class="winner-option nc-option" :class="{ active: fight.resultWinner === 'no_contest' }">
                <input v-model="fight.resultWinner" type="radio" value="no_contest" class="sr-only" />
                <span class="label-text">No Contest</span>
              </label>
            </div>
          </div>

          <div class="result-row">
            <div class="field field-sm">
              <label>Metodo</label>
              <Select
                v-model="fight.resultMethodId"
                :options="methodOptions"
                option-label="label"
                option-value="value"
                placeholder="Metodo..."
                class="w-full"
                :disabled="fight.resultWinner === 'draw' || fight.resultWinner === 'no_contest'"
              />
            </div>
            <div class="field field-sm" v-if="fight.resultWinner !== 'draw' && fight.resultWinner !== 'no_contest'">
              <label>Round</label>
              <Select
                v-model="fight.resultRound"
                :options="roundResultOptions"
                option-label="label"
                option-value="value"
                placeholder="Round..."
                class="w-full"
              />
            </div>
            <div class="field field-sm">
              <label>Tempo</label>
              <InputText v-model="fight.resultTime" placeholder="2:34" class="glass-input w-full" />
            </div>
          </div>

          <div class="result-actions">
            <Button
              :label="fight.saving ? 'Salvando...' : 'Salvar Resultado'"
              :loading="fight.saving"
              class="glass-button primary w-full"
              :disabled="!canSaveResult(fight)"
              @click="handleSaveResult(index)"
            />
            <p v-if="fight.saveError" class="text-red-400 text-xs mt-1">{{ fight.saveError }}</p>
            <p v-if="fight.saveOk" class="text-green-400 text-xs mt-1">{{ fight.saveOk }}</p>
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
import { ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import Select from 'primevue/select'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import FighterSelector from '@/components/ui/FighterSelector.vue'
import { api } from '@/services/api'
import type { Fighter, FightCreate, Fight } from '@/types'

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
  fightId?: string
  showResult: boolean
  resultWinner: string
  resultMethodId: string
  resultRound: number | null
  resultTime: string
  saving: boolean
  saveError: string
  saveOk: string
  existingResult?: string
  existingWinner?: string
  existingRound?: number
}

const props = defineProps<{
  modelValue: FightCreate[]
  eventId: string
  eventStatus?: string
  eventFights?: Fight[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: FightCreate[]]
  'result-saved': []
}>()

const positionOptions = [
  { label: 'Main Event', value: 'main' },
  { label: 'Co-Main', value: 'co-main' },
  { label: 'Main Card', value: 'main_card' },
  { label: 'Preliminar', value: 'preliminary' },
]

const weightClassOptions = ref<{ label: string; value: string }[]>([])
const finishMethods = ref<any[]>([])

const roundOptions = [
  { label: '3 Rounds', value: 3 },
  { label: '5 Rounds', value: 5 },
]

const roundResultOptions = [
  { label: '1', value: 1 },
  { label: '2', value: 2 },
  { label: '3', value: 3 },
  { label: '4', value: 4 },
  { label: '5', value: 5 },
]

const METHOD_GROUPS: Record<string, string> = {
  TKO: 'KO',
  'Technical Knockout': 'KO',
}

const methodOptions = ref<{ label: string; value: string }[]>([])

function canSaveResult(fight: FightSlot): boolean {
  if (fight.resultWinner === 'draw' || fight.resultWinner === 'no_contest') return true
  return !!fight.resultWinner && !!fight.resultMethodId
}

async function loadWeightClasses() {
  try {
    const classes = await api.getWeightClasses()
    weightClassOptions.value = classes.map((c: any) => ({
      label: c.name_pt || c.name,
      value: c.name,
    }))
  } catch {
    weightClassOptions.value = [
      { label: 'Flyweight', value: 'Flyweight' },
      { label: 'Bantamweight', value: 'Bantamweight' },
      { label: 'Featherweight', value: 'Featherweight' },
      { label: 'Lightweight', value: 'Lightweight' },
      { label: 'Welterweight', value: 'Welterweight' },
      { label: 'Middleweight', value: 'Middleweight' },
      { label: 'Light Heavyweight', value: 'Light Heavyweight' },
      { label: 'Heavyweight', value: 'Heavyweight' },
    ]
  }
}

async function loadMethods() {
  try {
    finishMethods.value = await api.getFinishMethods()
    const seen = new Set<string>()
    methodOptions.value = []
    for (const m of finishMethods.value) {
      const group = METHOD_GROUPS[m.code] || METHOD_GROUPS[m.name] || m.code
      if (seen.has(group)) continue
      seen.add(group)
      const grouped = finishMethods.value.filter(
        (x: any) => METHOD_GROUPS[x.code] === group || METHOD_GROUPS[x.name] === group || x.code === group
      )
      const names = [...new Set(grouped.map((x: any) => x.name_pt || x.name))]
      methodOptions.value.push({
        label: names.length > 1 ? names.join('/') : (m.name_pt || m.name),
        value: m.id || m.code,
      })
    }
  } catch {
    methodOptions.value = []
  }
}

function matchExistingResult(slot: FightSlot) {
  if (!props.eventFights) return
  const existing = props.eventFights.find((f: Fight) => {
    if (slot.fightId && f.id === slot.fightId) return true
    if (slot.fighter1_id && slot.fighter2_id) {
      return (f.fighter1_id === slot.fighter1_id && f.fighter2_id === slot.fighter2_id) ||
        (f.fighter1_id === slot.fighter2_id && f.fighter2_id === slot.fighter1_id)
    }
    return false
  })
  if (!existing) return

  slot.fightId = existing.id
  slot.existingResult = existing.result_type || undefined
  if (existing.winner) {
    slot.existingWinner = existing.winner.name || undefined
  }
  slot.existingRound = existing.finish_round || undefined

  if (existing.winner_id) {
    slot.resultWinner = existing.winner_id === existing.fighter1_id ? 'fighter1' : 'fighter2'
  } else if (existing.result_type?.toLowerCase() === 'draw') {
    slot.resultWinner = 'draw'
  } else if (existing.result_type?.toLowerCase() === 'no_contest') {
    slot.resultWinner = 'no_contest'
  }

  const currentMethod = existing.result_type || ''
  const matched = finishMethods.value.find(
    (m: any) => (m.name || m.code) === currentMethod
  )
  if (matched) {
    const group = METHOD_GROUPS[matched.code] || METHOD_GROUPS[matched.name]
    if (group) {
      const canonical = finishMethods.value.find(
        (m: any) => (m.code === group || m.name === group)
      )
      slot.resultMethodId = canonical?.id || canonical?.code || matched.id
    } else {
      slot.resultMethodId = matched.id || matched.code || currentMethod
    }
  } else {
    slot.resultMethodId = currentMethod
  }

  slot.resultRound = existing.finish_round || null
  slot.resultTime = existing.finish_time || ''
}

async function handleSaveResult(index: number) {
  const fight = fights.value[index]
  if (!fight || !props.eventId || props.eventId === 'new') return
  if (!fight.fightId) {
    fight.saveError = 'Luta ainda não foi salva no evento. Atualize o card de lutas primeiro.'
    return
  }
  fight.saveError = ''
  fight.saveOk = ''
  fight.saving = true

  let winnerId: string | null = null
  if (fight.resultWinner === 'fighter1' && fight.fighter1) {
    winnerId = fight.fighter1.id
  } else if (fight.resultWinner === 'fighter2' && fight.fighter2) {
    winnerId = fight.fighter2.id
  }

  const selectedMethod = finishMethods.value.find(
    (m: any) => (m.id || m.code) === fight.resultMethodId
  )
  const methodLabel = selectedMethod
    ? (selectedMethod.name_pt || selectedMethod.name || selectedMethod.code)
    : fight.resultMethodId
  const methodIdToSend = selectedMethod?.id || fight.resultMethodId

  try {
    await api.updateFightResult(props.eventId, fight.fightId || '', {
      winner_id: winnerId || '',
      method_id: methodIdToSend || '',
      method_details: methodLabel || '',
      finish_round: fight.resultRound || 0,
      finish_time: fight.resultTime || '',
    })
    fight.saveOk = 'Resultado salvo!'
    fight.showResult = false
    fight.existingResult = methodLabel || undefined
    fight.existingWinner = fight.resultWinner === 'fighter1' ? fight.fighter1?.name || undefined : fight.resultWinner === 'fighter2' ? fight.fighter2?.name || undefined : undefined
    fight.existingRound = fight.resultRound || undefined
    emit('result-saved')
  } catch (e: any) {
    fight.saveError = e.message || 'Erro ao salvar'
  } finally {
    fight.saving = false
  }
}

function createEmptySlot(): FightSlot {
  return {
    fighter1: null,
    fighter2: null,
    fight_type: 'main_card',
    weight_class: undefined,
    rounds: 3,
    is_title_fight: false,
    fight_order: 1,
    showResult: false,
    resultWinner: '',
    resultMethodId: '',
    resultRound: null,
    resultTime: '',
    saving: false,
    saveError: '',
    saveOk: '',
  }
}

onMounted(() => {
  loadWeightClasses()
  loadMethods()
})

const fights = ref<FightSlot[]>([])

watch(
  () => [props.modelValue, props.eventFights] as const,
  async (newVal, oldVal) => {
    const val = newVal[0]
    const oldKey = oldVal ? JSON.stringify([oldVal[0], oldVal[1]]) : ''
    const newKey = JSON.stringify([newVal[0], newVal[1]])
    if (newKey === oldKey) return

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
        showResult: false,
        resultWinner: '',
        resultMethodId: '',
        resultRound: null,
        resultTime: '',
        saving: false,
        saveError: '',
        saveOk: '',
      }))

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

      if (props.eventFights) {
        slots.forEach((s) => {
          if (!s.fighter1_id || !s.fighter2_id) return
          const existing = props.eventFights!.find(
            (f: Fight) =>
              (f.fighter1_id === s.fighter1_id && f.fighter2_id === s.fighter2_id) ||
              (f.fighter1_id === s.fighter2_id && f.fighter2_id === s.fighter1_id)
          )
          if (existing) s.fightId = existing.id
        })
      }

      fights.value = slots

      if (finishMethods.value.length > 0) {
        fights.value.forEach((s) => matchExistingResult(s))
      }
    }
  },
  { immediate: true },
)

watch(finishMethods, () => {
  fights.value.forEach((s) => matchExistingResult(s))
})

function getFightLabel(index: number): string {
  const total = fights.value.length
  const order = total - index
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
      fight_order: fights.value.length - i,
    }))
  if (JSON.stringify(result) === JSON.stringify(props.modelValue)) return
  emit('update:modelValue', result)
}

watch(fights, syncToModel, { deep: true })

function addFight() {
  fights.value.unshift(createEmptySlot())
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

.slot-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.result-badge-compact {
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
}

.result-ko, .result-tko { background: rgba(239, 68, 68, 0.2); color: #f87171; }
.result-submission { background: rgba(16, 185, 129, 0.2); color: #4ade80; }
.result-decision, .result-split-decision, .result-majority-decision { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
.result-dq { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
.result-draw { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
.result-no_contest { background: rgba(255, 255, 255, 0.1); color: var(--text-muted); }

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

.result-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.result-toggle-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--glass-border);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.result-toggle-btn:hover {
  background: rgba(124, 58, 237, 0.08);
  border-color: rgba(124, 58, 237, 0.3);
  color: var(--accent-light);
}

.rotate-180 {
  transform: rotate(180deg);
}

.result-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 12px;
  padding: 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.winner-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.winner-option {
  padding: 10px;
  border-radius: 8px;
  border: 1px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.03);
  cursor: pointer;
  text-align: center;
  transition: all 0.2s ease;
}

.winner-option:hover {
  background: rgba(255, 255, 255, 0.06);
}

.winner-option.active {
  border-color: var(--accent);
  background: rgba(124, 58, 237, 0.15);
  color: var(--accent-light);
}

.draw-option { grid-column: 1; }
.nc-option { grid-column: 2; }

.label-text {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
  pointer-events: none;
}

.winner-option.active .label-text {
  color: var(--accent-light);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
}

.result-actions {
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.result-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.field-sm label {
  font-size: 0.7rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.w-full { width: 100%; }

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
