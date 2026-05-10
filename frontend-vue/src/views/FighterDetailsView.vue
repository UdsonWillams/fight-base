<template>
  <div class="page-container">
    <button class="btn-icon mb-6" @click="$router.back()">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
      </svg>
      <span class="ml-2 text-sm">{{ t('common.back') }}</span>
    </button>

    <div v-if="fighterStore.loading" class="space-y-4">
      <div class="h-10 bg-white/10 rounded w-64 animate-pulse" />
      <div class="h-6 bg-white/5 rounded w-48 animate-pulse" />
      <div class="grid-3"><div v-for="i in 6" :key="i" class="glass-card p-6 animate-pulse"><div class="h-8 bg-white/10 rounded w-full mb-4" /><div class="h-4 bg-white/5 rounded w-3/4" /></div></div>
    </div>

    <template v-else-if="fighter">
      <div class="glass-card p-6 mb-8">
        <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <h1 class="text-3xl font-black text-white">{{ fighter.name }}</h1>
            <p v-if="fighter.nickname" class="text-lg text-purple-400 italic mt-1">"{{ fighter.nickname }}"</p>
            <div class="flex flex-wrap gap-2 mt-2">
              <span v-if="fighter.last_organization_fight" class="badge badge-blue">{{ fighter.last_organization_fight }}</span>
              <span v-if="fighter.actual_weight_class" class="badge badge-purple">{{ fighter.actual_weight_class }}</span>
              <span v-if="fighter.fighting_style" class="badge badge-green">{{ fighter.fighting_style }}</span>
            </div>
          </div>
          <div class="text-center md:text-right">
            <div class="text-5xl font-black" :class="overallColor">{{ fighter.overall_rating }}</div>
            <div class="text-xs text-white/30 uppercase tracking-widest">{{ t('fighters.overall') }}</div>
          </div>
        </div>
        <div v-if="authStore.isLoggedIn" class="flex gap-2 mt-4 pt-4 border-t border-white/5">
          <button class="glass-button text-sm !py-1.5 !px-4" @click="openEditDialog">{{ t('common.edit') }}</button>
          <button class="glass-button danger text-sm !py-1.5 !px-4" @click="confirmDelete">{{ t('common.delete') }}</button>
        </div>
      </div>

      <TabView class="glass-card !rounded-2xl" :pt="{ root: { class: '!bg-transparent' }, nav: { class: '!bg-transparent !border-b !border-white/10' }, panelContainer: { class: '!bg-transparent' } }">
        <TabPanel value="perfil" :header="t('fighters.profile')">
          <div class="p-4">
            <h3 class="text-lg font-semibold text-white/80 mb-4">{{ t('fighters.physical') }}</h3>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
              <div class="glass-card !p-3 text-center"><div class="text-2xl font-bold text-white">{{ fighter.height_cm || '-' }}</div><div class="text-xs text-white/40 mt-1">{{ t('fighters.height') }} (cm)</div></div>
              <div class="glass-card !p-3 text-center"><div class="text-2xl font-bold text-white">{{ fighter.weight || '-' }}</div><div class="text-xs text-white/40 mt-1">{{ t('fighters.weight') }} (kg)</div></div>
              <div class="glass-card !p-3 text-center"><div class="text-2xl font-bold text-white">{{ fighter.reach_cm || '-' }}</div><div class="text-xs text-white/40 mt-1">{{ t('fighters.reach') }} (cm)</div></div>
              <div class="glass-card !p-3 text-center"><div class="text-2xl font-bold text-white">{{ fighter.stance || '-' }}</div><div class="text-xs text-white/40 mt-1">{{ t('fighters.stance') }}</div></div>
            </div>

            <h3 class="text-lg font-semibold text-white/80 mb-4">{{ t('fighters.record') }}</h3>
            <div class="flex items-center gap-6 mb-8">
              <div class="text-center"><div class="text-3xl font-bold text-green-400">{{ fighter.wins }}</div><div class="text-xs text-white/40">{{ t('fighters.wins') }}</div></div>
              <div class="text-center"><div class="text-3xl font-bold text-red-400">{{ fighter.losses }}</div><div class="text-xs text-white/40">{{ t('fighters.losses') }}</div></div>
              <div class="text-center"><div class="text-3xl font-bold text-yellow-400">{{ fighter.draws }}</div><div class="text-xs text-white/40">{{ t('fighters.draws') }}</div></div>
            </div>
          </div>
        </TabPanel>

        <TabPanel value="atributos" :header="t('fighters.attributes')">
          <div class="p-4 space-y-5 max-w-lg">
            <AttributeBar :label="t('fighters.striking')" :value="fighter.striking" />
            <AttributeBar :label="t('fighters.grappling')" :value="fighter.grappling" />
            <AttributeBar :label="t('fighters.defense')" :value="fighter.defense" />
            <AttributeBar :label="t('fighters.stamina')" :value="fighter.stamina" />
            <AttributeBar :label="t('fighters.speed')" :value="fighter.speed" />
            <AttributeBar :label="t('fighters.strategy')" :value="fighter.strategy" />
          </div>
        </TabPanel>

        <TabPanel value="estatisticas" :header="t('fighters.statistics')">
          <div class="p-4">
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div class="glass-card !p-3 text-center"><div class="text-xl font-bold text-purple-400">{{ fighter.slpm ?? '-' }}</div><div class="text-xs text-white/40 mt-1">{{ t('fighters.slpm') }}</div></div>
              <div class="glass-card !p-3 text-center"><div class="text-xl font-bold text-purple-400">{{ fighter.str_acc != null ? fighter.str_acc + '%' : '-' }}</div><div class="text-xs text-white/40 mt-1">{{ t('fighters.strAcc') }}</div></div>
              <div class="glass-card !p-3 text-center"><div class="text-xl font-bold text-purple-400">{{ fighter.sapm ?? '-' }}</div><div class="text-xs text-white/40 mt-1">{{ t('fighters.sapm') }}</div></div>
              <div class="glass-card !p-3 text-center"><div class="text-xl font-bold text-purple-400">{{ fighter.str_def != null ? fighter.str_def + '%' : '-' }}</div><div class="text-xs text-white/40 mt-1">{{ t('fighters.strDef') }}</div></div>
              <div class="glass-card !p-3 text-center"><div class="text-xl font-bold text-purple-400">{{ fighter.td_avg ?? '-' }}</div><div class="text-xs text-white/40 mt-1">{{ t('fighters.tdAvg') }}</div></div>
              <div class="glass-card !p-3 text-center"><div class="text-xl font-bold text-purple-400">{{ fighter.td_acc != null ? fighter.td_acc + '%' : '-' }}</div><div class="text-xs text-white/40 mt-1">{{ t('fighters.tdAcc') }}</div></div>
              <div class="glass-card !p-3 text-center"><div class="text-xl font-bold text-purple-400">{{ fighter.td_def != null ? fighter.td_def + '%' : '-' }}</div><div class="text-xs text-white/40 mt-1">{{ t('fighters.tdDef') }}</div></div>
              <div class="glass-card !p-3 text-center"><div class="text-xl font-bold text-purple-400">{{ fighter.sub_avg ?? '-' }}</div><div class="text-xs text-white/40 mt-1">{{ t('fighters.subAvg') }}</div></div>
            </div>
          </div>
        </TabPanel>

        <TabPanel value="cartel" :header="t('fighters.record')">
          <div class="p-4">
            <div v-if="fighter.cartel" class="whitespace-pre-wrap text-sm text-white/60 glass-card !p-4">{{ fighter.cartel }}</div>
            <div v-else class="empty-state !py-8"><p class="text-sm">Nenhum histórico de lutas registrado.</p></div>
          </div>
        </TabPanel>
      </TabView>
    </template>

    <div v-else class="empty-state"><p class="text-lg">Lutador não encontrado.</p></div>

    <Dialog v-model:visible="showEditDialog" :header="t('fighters.editFighter')" :modal="true" :style="{ width: '720px' }" class="glass-card" :pt="{ header: { class: '!bg-transparent !border-b !border-white/5 !text-white !px-6 !py-4' }, content: { class: '!bg-transparent !px-6 !pb-6' } }">
      <FighterForm v-if="fighter" :fighter="fighter" @save="handleEdit" @cancel="showEditDialog = false" />
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import Dialog from 'primevue/dialog'
import AttributeBar from '@/components/ui/AttributeBar.vue'
import FighterForm from '@/components/fighters/FighterForm.vue'
import { useAuthStore } from '@/stores/auth'
import { useFighterStore } from '@/stores/fighters'
import type { FighterCreate } from '@/types'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const toast = useToast()
const confirm = useConfirm()
const authStore = useAuthStore()
const fighterStore = useFighterStore()

const showEditDialog = ref(false)

const fighter = computed(() => fighterStore.currentFighter)

const overallColor = computed(() => {
  const ov = fighter.value?.overall_rating || 0
  if (ov >= 80) return 'text-green-400'
  if (ov >= 60) return 'text-yellow-400'
  if (ov >= 40) return 'text-orange-400'
  return 'text-red-400'
})

function openEditDialog() { showEditDialog.value = true }

async function handleEdit(data: FighterCreate) {
  if (!fighter.value) return
  try {
    await fighterStore.updateFighter(fighter.value.id, data)
    toast.add({ severity: 'success', summary: t('common.success'), detail: 'Lutador atualizado!', life: 3000 })
    showEditDialog.value = false
  } catch {
    toast.add({ severity: 'error', summary: t('common.error'), detail: fighterStore.error || t('common.error'), life: 5000 })
  }
}

function confirmDelete() {
  confirm.require({
    message: t('fighters.deleteConfirm'),
    header: t('fighters.deleteFighter'),
    acceptClass: 'glass-button danger',
    rejectClass: 'glass-button',
    accept: async () => {
      if (!fighter.value) return
      try {
        await fighterStore.deleteFighter(fighter.value.id)
        toast.add({ severity: 'success', summary: t('common.success'), detail: 'Lutador deletado!', life: 3000 })
        router.push('/fighters')
      } catch {
        toast.add({ severity: 'error', summary: t('common.error'), detail: fighterStore.error || t('common.error'), life: 5000 })
      }
    },
  })
}

onMounted(() => {
  const id = route.params.id as string
  if (id) fighterStore.fetchFighter(id)
})
</script>
