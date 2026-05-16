<template>
  <div class="page-container">
    <div class="flex items-center justify-between mb-8">
      <h1 class="section-title !mb-0">{{ t('fighters.title') }}</h1>
      <Button v-if="authStore.isLoggedIn" class="glass-button primary" :label="t('fighters.createFighter')" @click="openCreateDialog" />
    </div>

    <div class="glass-card p-4 mb-8">
      <div class="flex flex-col md:flex-row gap-4">
        <div class="flex-1">
          <InputText v-model="searchQuery" class="glass-input w-full" :placeholder="t('fighters.search')" @input="onSearch" />
        </div>
        <div class="flex gap-3 flex-wrap items-center">
          <Select v-model="filterOrganization" :options="organizations" :placeholder="t('fighters.organization')" option-label="label" option-value="value" class="w-full md:w-48" panel-class="!bg-gray-900 !border-white/10" show-clear @change="applyFilters" />
          <Select v-model="filterWeightClass" :options="weightClasses" :placeholder="t('fighters.weightClass')" option-label="label" option-value="value" class="w-full md:w-48" panel-class="!bg-gray-900 !border-white/10" show-clear @change="applyFilters" />
          <Select v-model="filterStyle" :options="styles" :placeholder="t('fighters.fightingStyle')" option-label="label" option-value="value" class="w-full md:w-48" panel-class="!bg-gray-900 !border-white/10" show-clear @change="applyFilters" />
          <Select v-model="sortBy" :options="sortOptions" placeholder="Ordenar por" option-label="label" option-value="value" class="w-full md:w-48" panel-class="!bg-gray-900 !border-white/10" show-clear @change="applyFilters" />
          <button class="glass-button text-sm !py-2 !px-4" @click="toggleSortOrder">
            {{ sortOrderLabel }}
          </button>
          <label class="flex items-center gap-2 cursor-pointer select-none">
            <input type="checkbox" v-model="filterActiveOnly" class="w-4 h-4 accent-purple-500 rounded" @change="applyFilters" />
            <span class="text-sm text-white/80">Apenas Ativos</span>
          </label>
        </div>
      </div>
    </div>

    <div v-if="fighterStore.loading" class="grid-3">
      <SkeletonCard v-for="i in 6" :key="i" />
    </div>

    <div v-else-if="fighterStore.fighters.length === 0" class="empty-state">
      <div class="empty-state-icon">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" class="mx-auto">
          <circle cx="12" cy="12" r="10" /><path d="M8 14s1.5 2 4 2 4-2 4-2" /><line x1="9" y1="9" x2="9.01" y2="9" /><line x1="15" y1="9" x2="15.01" y2="9" />
        </svg>
      </div>
      <p class="text-lg">
        {{ filterActiveOnly ? 'Nenhum lutador ativo encontrado com estes filtros.' : t('fighters.noFighters') }}
      </p>
      <p v-if="filterActiveOnly" class="text-sm text-white/40 mt-2">Desmarque "Apenas Ativos" para ver todos.</p>
    </div>

    <div v-else class="grid-3">
      <FighterCard v-for="fighter in fighterStore.fighters" :key="fighter.id" :fighter="fighter" clickable @click="goToFighter" />
    </div>

    <Dialog v-model:visible="showDialog" :header="editingFighter ? t('fighters.editFighter') : t('fighters.createFighter')" :modal="true" :style="{ width: '720px' }" class="glass-card" :pt="{ header: { class: '!bg-transparent !border-b !border-white/5 !text-white !px-6 !py-4' }, content: { class: '!bg-transparent !px-6 !pb-6' } }">
      <FighterForm :fighter="editingFighter" @save="handleFormSubmit" @cancel="showDialog = false" />
    </Dialog>

    <ConfirmDialog group="fighter-delete" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import { useDebounceFn } from '@vueuse/core'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import ConfirmDialog from 'primevue/confirmdialog'
import FighterCard from '@/components/fighters/FighterCard.vue'
import FighterForm from '@/components/fighters/FighterForm.vue'
import SkeletonCard from '@/components/ui/SkeletonCard.vue'
import { useAuthStore } from '@/stores/auth'
import { useFighterStore } from '@/stores/fighters'
import type { Fighter, FighterCreate } from '@/types'

const router = useRouter()
const { t } = useI18n()
const toast = useToast()
const authStore = useAuthStore()
const fighterStore = useFighterStore()

const searchQuery = ref('')
const filterOrganization = ref<string | null>(null)
const filterWeightClass = ref<string | null>(null)
const filterStyle = ref<string | null>(null)
const filterActiveOnly = ref(true)
const sortBy = ref<string>('overall')
const sortOrder = ref<string>('desc')
const showDialog = ref(false)
const editingFighter = ref<Fighter | null>(null)

const organizations = [
  { label: 'UFC', value: 'UFC' },
  { label: 'Bellator', value: 'Bellator' },
  { label: 'ONE Championship', value: 'ONE Championship' },
  { label: 'PFL', value: 'PFL' },
]

const weightClasses = [
  { label: 'Flyweight', value: 'Flyweight' },
  { label: 'Bantamweight', value: 'Bantamweight' },
  { label: 'Featherweight', value: 'Featherweight' },
  { label: 'Lightweight', value: 'Lightweight' },
  { label: 'Welterweight', value: 'Welterweight' },
  { label: 'Middleweight', value: 'Middleweight' },
  { label: 'Light Heavyweight', value: 'Light Heavyweight' },
  { label: 'Heavyweight', value: 'Heavyweight' },
]

const styles = [
  { label: 'Boxe', value: 'Boxe' },
  { label: 'Muay Thai', value: 'Muay Thai' },
  { label: 'Jiu-Jitsu', value: 'Jiu-Jitsu' },
  { label: 'Wrestling', value: 'Wrestling' },
  { label: 'Kickboxing', value: 'Kickboxing' },
  { label: 'Karate', value: 'Karate' },
]

const sortOptions = [
  { label: 'Overall', value: 'overall' },
  { label: 'Nome', value: 'name' },
  { label: 'Ultima Luta', value: 'last_fight_date' },
]

const sortOrderLabel = computed(() => sortOrder.value === 'desc' ? '↓' : '↑')

function toggleSortOrder() {
  sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
  applyFilters()
}

const debouncedSearch = useDebounceFn(() => { applyFilters() }, 300)

function onSearch() { debouncedSearch() }

function applyFilters() {
  const params: Record<string, string | number | boolean> = {}
  if (searchQuery.value) params.name = searchQuery.value
  if (filterOrganization.value) params.last_organization_fight = filterOrganization.value
  if (filterWeightClass.value) params.actual_weight_class = filterWeightClass.value
  if (filterStyle.value) params.fighting_style = filterStyle.value
  if (sortBy.value) params.sort_by = sortBy.value
  if (sortOrder.value) params.sort_order = sortOrder.value
  params.recent_activity = filterActiveOnly.value
  params.limit = 50
  fighterStore.fetchFighters(params)
}

function goToFighter(fighter: Fighter) {
  router.push(`/fighters/${fighter.id}`)
}

function openCreateDialog() {
  editingFighter.value = null
  showDialog.value = true
}

async function handleFormSubmit(data: FighterCreate) {
  try {
    if (editingFighter.value) {
      await fighterStore.updateFighter(editingFighter.value.id, data)
      toast.add({ severity: 'success', summary: t('common.success'), detail: 'Lutador atualizado!', life: 3000 })
    } else {
      await fighterStore.createFighter(data)
      toast.add({ severity: 'success', summary: t('common.success'), detail: 'Lutador criado!', life: 3000 })
    }
    showDialog.value = false
    editingFighter.value = null
  } catch {
    toast.add({ severity: 'error', summary: t('common.error'), detail: fighterStore.error || t('common.error'), life: 5000 })
  }
}

onMounted(() => {
  applyFilters()
  fighterStore.fetchStats()
})
</script>
