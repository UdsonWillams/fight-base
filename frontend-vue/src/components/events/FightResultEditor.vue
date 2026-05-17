<template>
  <div class="result-editor glass-card">
    <div class="fight-header">
      <span class="fighter-name">{{ fighter1Name }}</span>
      <span class="vs-text">VS</span>
      <span class="fighter-name">{{ fighter2Name }}</span>
    </div>

    <div v-if="fight?.result_type" class="current-result mb-4">
      <span class="result-badge" :class="'result-' + (fight.result_type || '').toLowerCase()">
        {{ fight.result_type }}
      </span>
      <span v-if="fight.winner" class="text-white/60 text-sm">
        — {{ fight.winner.name }} venceu
      </span>
      <span v-if="fight.finish_round" class="text-white/40 text-sm">
        no R{{ fight.finish_round }}
      </span>
    </div>

    <div class="result-form">
      <div class="field">
        <label>Vencedor</label>
        <div class="winner-options">
          <label class="winner-option" :class="{ active: result.winner === 'fighter1' }">
            <input v-model="result.winner" type="radio" value="fighter1" class="sr-only" />
            <span class="label-text">{{ fighter1Name }}</span>
          </label>
          <label class="winner-option" :class="{ active: result.winner === 'fighter2' }">
            <input v-model="result.winner" type="radio" value="fighter2" class="sr-only" />
            <span class="label-text">{{ fighter2Name }}</span>
          </label>
          <label class="winner-option draw-option" :class="{ active: result.winner === 'draw' }">
            <input v-model="result.winner" type="radio" value="draw" class="sr-only" />
            <span class="label-text">Empate</span>
          </label>
          <label class="winner-option nc-option" :class="{ active: result.winner === 'no_contest' }">
            <input v-model="result.winner" type="radio" value="no_contest" class="sr-only" />
            <span class="label-text">No Contest</span>
          </label>
        </div>
      </div>

      <div class="field">
        <label>Método</label>
        <Select
          v-model="result.method"
          :options="methodOptions"
          option-label="label"
          option-value="value"
          placeholder="Selecionar método..."
          class="w-full"
          :disabled="result.winner === 'draw' || result.winner === 'no_contest'"
        />
      </div>

      <div class="field" v-if="result.winner !== 'draw' && result.winner !== 'no_contest'">
        <label>Round</label>
        <Select
          v-model="result.round"
          :options="roundOptions"
          option-label="label"
          option-value="value"
          placeholder="Round..."
          class="w-full"
        />
      </div>

      <div class="field">
        <label>Tempo (opcional)</label>
        <InputText v-model="result.time" placeholder="ex: 2:34" class="glass-input w-full" />
      </div>
    </div>

    <div class="result-actions">
      <Button
        :label="saving ? 'Salvando...' : 'Salvar Resultado'"
        icon="pi pi-check"
        :loading="saving"
        class="glass-button primary w-full"
        :disabled="!canSave"
        @click="handleSave"
      />
      <p v-if="saveError" class="text-red-400 text-sm mt-2">{{ saveError }}</p>
      <p v-if="saveOk" class="text-green-400 text-sm mt-2">{{ saveOk }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import Select from 'primevue/select'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import { api } from '@/services/api'
import type { Fight } from '@/types'

const { t } = useI18n()
const toast = useToast()

const props = defineProps<{
  eventId: string
  fight: Fight | null
  fighter1Name: string
  fighter2Name: string
}>()

const emit = defineEmits<{
  saved: []
}>()

const result = ref<{
  winner: string
  method: string
  round: number | null
  time: string
}>({
  winner: '',
  method: '',
  round: null,
  time: '',
})

const saving = ref(false)
const saveError = ref('')
const saveOk = ref('')

const methodOptions = [
  { label: 'KO', value: 'KO' },
  { label: 'TKO', value: 'TKO' },
  { label: 'Submissão', value: 'Submission' },
  { label: 'Decisão Unânime', value: 'Decision' },
  { label: 'Decisão Dividida', value: 'Split Decision' },
  { label: 'Decisão Majoritária', value: 'Majority Decision' },
  { label: 'Desqualificação', value: 'DQ' },
]

const roundOptions = [
  { label: '1', value: 1 },
  { label: '2', value: 2 },
  { label: '3', value: 3 },
  { label: '4', value: 4 },
  { label: '5', value: 5 },
]

const canSave = computed(() => {
  if (result.value.winner === 'draw' || result.value.winner === 'no_contest') return true
  return result.value.winner && result.value.method
})

watch(
  () => props.fight,
  (f) => {
    if (f?.winner_id) {
      const isFighter1 = f.winner_id === f.fighter1_id
      const isFighter2 = f.winner_id === f.fighter2_id
      const isDraw = f.result_type?.toLowerCase() === 'draw'
      const isNC = f.result_type?.toLowerCase() === 'no_contest'

      result.value = {
        winner: isFighter1 ? 'fighter1' : isFighter2 ? 'fighter2' : isDraw ? 'draw' : isNC ? 'no_contest' : '',
        method: f.result_type || '',
        round: f.finish_round || null,
        time: f.finish_time || '',
      }
    }
  },
  { immediate: true },
)

async function handleSave() {
  if (!props.fight || !props.eventId) return
  saveError.value = ''
  saveOk.value = ''
  saving.value = true

  let winnerId: string | null = null
  let methodDetails = result.value.method
  const resultType = result.value.method

  if (result.value.winner === 'fighter1') {
    winnerId = props.fight.fighter1_id
  } else if (result.value.winner === 'fighter2') {
    winnerId = props.fight.fighter2_id
  }

  try {
    await api.updateFightResult(props.eventId, props.fight.id, {
      winner_id: winnerId || '',
      method_details: methodDetails,
      finish_round: result.value.round || 0,
      finish_time: result.value.time || '',
    })
    saveOk.value = 'Resultado salvo!'
    toast.add({ severity: 'success', summary: 'OK', detail: 'Resultado salvo!', life: 2000 })
    emit('saved')
  } catch (e: any) {
    saveError.value = e.message || 'Erro ao salvar'
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.result-editor {
  padding: 1.25rem;
}

.fight-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--glass-border);
}

.fighter-name {
  font-weight: 700;
  color: var(--text-primary);
  font-size: 1rem;
}

.vs-text {
  font-size: 0.75rem;
  font-weight: 900;
  color: var(--text-muted);
  letter-spacing: 2px;
}

.current-result {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.result-badge {
  padding: 2px 10px;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
}

.result-ko { background: rgba(239, 68, 68, 0.2); color: var(--danger); }
.result-tko { background: rgba(239, 68, 68, 0.2); color: var(--danger); }
.result-submission { background: rgba(16, 185, 129, 0.2); color: var(--success); }
.result-decision { background: rgba(59, 130, 246, 0.2); color: var(--primary-light); }
.result-split-decision, .result-majority-decision { background: rgba(59, 130, 246, 0.2); color: var(--primary-light); }
.result-dq { background: rgba(245, 158, 11, 0.2); color: var(--gold); }
.result-draw { background: rgba(245, 158, 11, 0.2); color: var(--gold); }
.result-no_contest { background: rgba(255, 255, 255, 0.1); color: var(--text-muted); }

.result-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field label {
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-weight: 500;
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

.winner-option.draw-option {
  grid-column: 1;
}

.winner-option.nc-option {
  grid-column: 2;
}

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
  padding-top: 12px;
  border-top: 1px solid var(--glass-border);
}

.w-full {
  width: 100%;
}
</style>
