<template>
  <div class="fighter-form glass-card">
    <h2 class="form-title">{{ fighter ? t('fighter.edit') : t('fighter.create') }}</h2>

    <div class="form-section">
      <h3 class="section-title">Informações Básicas</h3>
      <div class="form-grid">
        <div class="field">
          <label>{{ t('fighter.name') }} *</label>
          <InputText v-model="form.name" :placeholder="t('fighter.name')" class="w-full" />
        </div>
        <div class="field">
          <label>{{ t('fighter.nickname') }}</label>
          <InputText v-model="form.nickname" :placeholder="t('fighter.nickname')" class="w-full" />
        </div>
        <div class="field">
          <label>{{ t('fighter.organization') }} *</label>
          <Select v-model="form.last_organization_fight" :options="orgOptions" :placeholder="t('fighter.organization')" class="w-full" />
        </div>
        <div class="field">
          <label>{{ t('fighter.weightClass') }} *</label>
          <Select v-model="form.actual_weight_class" :options="weightOptions" :placeholder="t('fighter.weightClass')" class="w-full" />
        </div>
        <div class="field">
          <label>{{ t('fighter.stance') }}</label>
          <Select v-model="form.stance" :options="stanceOptions" :placeholder="t('fighter.stance')" class="w-full" />
        </div>
        <div class="field">
          <label>{{ t('fighter.gender') }}</label>
          <Select v-model="form.gender" :options="genderOptions" :placeholder="t('fighter.gender')" class="w-full" />
        </div>
        <div class="field">
          <label>{{ t('fighter.fightingStyle') }} *</label>
          <Select v-model="form.fighting_style" :options="styleOptions" :placeholder="t('fighter.fightingStyle')" class="w-full" />
        </div>
        <div class="field checkbox-field">
          <div class="checkbox-wrapper">
            <Checkbox v-model="form.is_real" :binary="true" inputId="is_real" />
            <label for="is_real">{{ t('fighter.isReal') }}</label>
          </div>
        </div>
      </div>
    </div>

    <div class="form-section">
      <h3 class="section-title">Medidas</h3>
      <div class="form-grid cols-3">
        <div class="field">
          <label>{{ t('fighter.height') }}</label>
          <InputNumber v-model="form.height_cm" :placeholder="t('fighter.height')" :min="150" :max="230" class="w-full" />
        </div>
        <div class="field">
          <label>{{ t('fighter.weight') }}</label>
          <InputNumber v-model="form.weight" :placeholder="t('fighter.weight')" :min="100" :max="300" class="w-full" />
        </div>
        <div class="field">
          <label>{{ t('fighter.reach') }}</label>
          <InputNumber v-model="form.reach_cm" :placeholder="t('fighter.reach')" :min="150" :max="250" class="w-full" />
        </div>
      </div>
    </div>

    <div class="form-section">
      <h3 class="section-title">Cartel</h3>
      <div class="form-grid cols-3">
        <div class="field">
          <label>{{ t('fighter.wins') }}</label>
          <InputNumber v-model="form.wins" :min="0" class="w-full" />
        </div>
        <div class="field">
          <label>{{ t('fighter.losses') }}</label>
          <InputNumber v-model="form.losses" :min="0" class="w-full" />
        </div>
        <div class="field">
          <label>{{ t('fighter.draws') }}</label>
          <InputNumber v-model="form.draws" :min="0" class="w-full" />
        </div>
      </div>
    </div>

    <div class="form-section">
      <h3 class="section-title">{{ t('fighter.attributes') }}</h3>
      <div class="attributes-grid">
        <div v-for="attr in attributes" :key="attr.key" class="attr-field">
          <label>{{ t(`fighter.${attr.key}`) }}</label>
          <div class="slider-row">
            <Slider v-model="form[attr.key]" :min="0" :max="100" :step="1" class="attr-slider" />
            <span class="slider-value">{{ form[attr.key] }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="form-section">
      <div class="expandable-header" @click="showAdvanced = !showAdvanced">
        <h3 class="section-title">{{ t('fighter.advancedStats') }}</h3>
        <span class="expand-icon">{{ showAdvanced ? '&#9650;' : '&#9660;' }}</span>
      </div>
      <div v-if="showAdvanced" class="form-grid cols-4">
        <div class="field">
          <label>{{ t('fighter.slpm') }}</label>
          <InputNumber v-model="form.slpm" :min="0" :max="20" :step="0.01" class="w-full" />
        </div>
        <div class="field">
          <label>{{ t('fighter.strAcc') }}</label>
          <InputNumber v-model="form.str_acc" :min="0" :max="100" :step="0.01" class="w-full" />
        </div>
        <div class="field">
          <label>{{ t('fighter.sapm') }}</label>
          <InputNumber v-model="form.sapm" :min="0" :max="20" :step="0.01" class="w-full" />
        </div>
        <div class="field">
          <label>{{ t('fighter.strDef') }}</label>
          <InputNumber v-model="form.str_def" :min="0" :max="100" :step="0.01" class="w-full" />
        </div>
        <div class="field">
          <label>{{ t('fighter.tdAvg') }}</label>
          <InputNumber v-model="form.td_avg" :min="0" :max="10" :step="0.01" class="w-full" />
        </div>
        <div class="field">
          <label>{{ t('fighter.tdAcc') }}</label>
          <InputNumber v-model="form.td_acc" :min="0" :max="100" :step="0.01" class="w-full" />
        </div>
        <div class="field">
          <label>{{ t('fighter.tdDef') }}</label>
          <InputNumber v-model="form.td_def" :min="0" :max="100" :step="0.01" class="w-full" />
        </div>
        <div class="field">
          <label>{{ t('fighter.subAvg') }}</label>
          <InputNumber v-model="form.sub_avg" :min="0" :max="5" :step="0.01" class="w-full" />
        </div>
      </div>
    </div>

    <div class="form-actions">
      <Button :label="t('fighter.cancel')" severity="secondary" outlined @click="$emit('cancel')" />
      <Button :label="t('fighter.save')" severity="success" @click="handleSave" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Select from 'primevue/select'
import Slider from 'primevue/slider'
import Checkbox from 'primevue/checkbox'
import Button from 'primevue/button'
import type { Fighter, FighterCreate } from '@/types'

const { t } = useI18n()

const props = defineProps<{
  fighter: Fighter | null
}>()

const emit = defineEmits<{
  save: [data: FighterCreate]
  cancel: []
}>()

const showAdvanced = ref(false)

const orgOptions = ['UFC', 'Bellator', 'ONE', 'PFL', 'Rizin', 'Glory', 'K-1', 'Custom', 'Other']
const weightOptions = [
  'Peso Palha', 'Peso Mosca', 'Peso Galo', 'Peso Pena',
  'Peso Leve', 'Peso Meio-Médio', 'Peso Médio', 'Peso Meio-Pesado',
  'Peso Pesado', 'Peso Combinado',
]
const stanceOptions = ['Ortodoxa', 'Canhota', 'Alternante', 'Aberta']
const genderOptions = ['Masculino', 'Feminino']
const styleOptions = [
  'Boxing', 'Muay Thai', 'Kickboxing', 'Jiu-Jitsu', 'Wrestling',
  'Judo', 'Karate', 'Taekwondo', 'Sambo', 'MMA',
]

interface FighterFormData extends Record<string, any> {
  name: string
  nickname: string
  last_organization_fight: string
  actual_weight_class: string
  stance: string
  gender: string
  fighting_style: string
  is_real: boolean
  height_cm: number | null
  weight: number | null
  reach_cm: number | null
  wins: number
  losses: number
  draws: number
  striking: number
  grappling: number
  defense: number
  stamina: number
  speed: number
  strategy: number
  slpm: number | null
  str_acc: number | null
  sapm: number | null
  str_def: number | null
  td_avg: number | null
  td_acc: number | null
  td_def: number | null
  sub_avg: number | null
}

const attributes = [
  { key: 'striking' },
  { key: 'grappling' },
  { key: 'defense' },
  { key: 'stamina' },
  { key: 'speed' },
  { key: 'strategy' },
]

const defaultForm = (): FighterFormData => ({
  name: '',
  nickname: '',
  last_organization_fight: '',
  actual_weight_class: '',
  stance: '',
  gender: '',
  fighting_style: '',
  is_real: false,
  height_cm: null,
  weight: null,
  reach_cm: null,
  wins: 0,
  losses: 0,
  draws: 0,
  striking: 50,
  grappling: 50,
  defense: 50,
  stamina: 50,
  speed: 50,
  strategy: 50,
  slpm: null,
  str_acc: null,
  sapm: null,
  str_def: null,
  td_avg: null,
  td_acc: null,
  td_def: null,
  sub_avg: null,
})

const form = reactive<FighterFormData>(defaultForm())

watch(
  () => props.fighter,
  (f) => {
    if (f) {
      form.name = f.name
      form.nickname = f.nickname || ''
      form.last_organization_fight = f.last_organization_fight || ''
      form.actual_weight_class = f.actual_weight_class || ''
      form.stance = f.stance || ''
      form.gender = f.gender || ''
      form.fighting_style = f.fighting_style || ''
      form.is_real = f.is_real
      form.height_cm = f.height_cm
      form.weight = f.weight
      form.reach_cm = f.reach_cm
      form.wins = f.wins
      form.losses = f.losses
      form.draws = f.draws
      form.striking = f.striking
      form.grappling = f.grappling
      form.defense = f.defense
      form.stamina = f.stamina
      form.speed = f.speed
      form.strategy = f.strategy
      form.slpm = f.slpm
      form.str_acc = f.str_acc
      form.sapm = f.sapm
      form.str_def = f.str_def
      form.td_avg = f.td_avg
      form.td_acc = f.td_acc
      form.td_def = f.td_def
      form.sub_avg = f.sub_avg
    } else {
      Object.assign(form, defaultForm())
    }
  },
  { immediate: true },
)

function handleSave() {
  const data: FighterCreate = {
    name: form.name,
    nickname: form.nickname || undefined,
    last_organization_fight: form.last_organization_fight,
    actual_weight_class: form.actual_weight_class,
    stance: form.stance || undefined,
    gender: form.gender || undefined,
    fighting_style: form.fighting_style,
    is_real: form.is_real,
    height_cm: form.height_cm ?? undefined,
    weight: form.weight ?? undefined,
    reach_cm: form.reach_cm ?? undefined,
    wins: form.wins,
    losses: form.losses,
    draws: form.draws,
    striking: form.striking,
    grappling: form.grappling,
    defense: form.defense,
    stamina: form.stamina,
    speed: form.speed,
    strategy: form.strategy,
    slpm: form.slpm ?? undefined,
    str_acc: form.str_acc ?? undefined,
    sapm: form.sapm ?? undefined,
    str_def: form.str_def ?? undefined,
    td_avg: form.td_avg ?? undefined,
    td_acc: form.td_acc ?? undefined,
    td_def: form.td_def ?? undefined,
    sub_avg: form.sub_avg ?? undefined,
  }
  emit('save', data)
}
</script>

<style scoped>
.fighter-form {
  padding: 2rem;
  max-width: 900px;
  margin: 0 auto;
}

.form-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 1.5rem;
}

.form-section {
  margin-bottom: 1.5rem;
}

.section-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--glass-border);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

.form-grid.cols-3 {
  grid-template-columns: repeat(3, 1fr);
}

.form-grid.cols-4 {
  grid-template-columns: repeat(4, 1fr);
}

.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field label {
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.w-full {
  width: 100%;
}

.checkbox-field {
  justify-content: flex-end;
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 20px;
}

.checkbox-wrapper label {
  cursor: pointer;
}

.attributes-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

.attr-field label {
  display: block;
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 4px;
}

.slider-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.attr-slider {
  flex: 1;
}

.slider-value {
  font-weight: 700;
  font-size: 0.9rem;
  color: var(--text-primary);
  min-width: 28px;
  text-align: right;
}

.expandable-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
}

.expand-icon {
  color: var(--text-muted);
  font-size: 0.75rem;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--glass-border);
}
</style>
