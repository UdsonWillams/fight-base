<template>
  <div class="page-container">
    <div class="flex items-center justify-between mb-8">
      <h1 class="section-title !mb-0">{{ t("leagues.title") }}</h1>
      <div class="flex gap-3">
        <Button class="glass-button primary text-sm" :label="t('leagues.createLeague')" @click="showCreateDialog = true" />
        <Button class="glass-button text-sm" :label="t('leagues.joinLeague')" @click="showJoinDialog = true" />
      </div>
    </div>

    <div v-if="predictionStore.loading" class="grid-3">
      <div v-for="i in 6" :key="i" class="glass-card p-5 animate-pulse">
        <div class="h-5 bg-white/10 rounded w-3/4 mb-3" />
        <div class="h-4 bg-white/5 rounded w-full mb-4" />
        <div class="flex gap-2">
          <div class="h-5 bg-white/10 rounded-full w-16" />
          <div class="h-5 bg-white/10 rounded-full w-20" />
        </div>
      </div>
    </div>

    <div v-else-if="predictionStore.leagues.length === 0" class="empty-state">
      <div class="empty-state-icon">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" class="mx-auto">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
      </div>
      <p class="text-lg">{{ t('leagues.noLeagues') }}</p>
      <p class="text-sm text-white/30 mt-2">Crie ou entre em uma liga para começar.</p>
    </div>

    <div v-else class="grid-3">
      <div v-for="league in predictionStore.leagues" :key="league.id" class="glass-card p-5">
        <h3 class="text-lg font-bold text-white mb-1">{{ league.name }}</h3>
        <p v-if="league.description" class="text-sm text-white/50 mb-4 line-clamp-2">{{ league.description }}</p>
        <p v-else class="text-sm text-white/20 italic mb-4">Sem descrição</p>

        <div class="flex flex-wrap gap-2 mb-3">
          <span class="badge badge-blue text-xs">{{ league.members_count }} {{ league.members_count === 1 ? 'membro' : 'membros' }}</span>
          <span class="badge badge-purple text-xs">{{ league.invite_code }}</span>
        </div>

        <div class="flex items-center gap-2 pt-3 border-t border-white/5">
          <button class="text-xs text-purple-400 hover:text-purple-300 transition-colors" @click="copyInviteCode(league.invite_code)">Copiar código</button>
        </div>
      </div>
    </div>

    <Dialog v-model:visible="showCreateDialog" :header="t('leagues.createLeague')" :modal="true" class="glass-card" :pt="{ header: { class: '!bg-transparent !border-b !border-white/5 !text-white !px-6 !py-4' }, content: { class: '!bg-transparent !px-6 !pb-6' } }">
      <div class="space-y-4 pt-2">
        <div><label class="block text-sm font-medium text-white/60 mb-2">{{ t('leagues.name') }} *</label><InputText v-model="createForm.name" class="glass-input w-full" required /></div>
        <div><label class="block text-sm font-medium text-white/60 mb-2">{{ t('leagues.description') }}</label><InputText v-model="createForm.description" class="glass-input w-full" /></div>
        <div class="flex justify-end gap-3 pt-4">
          <Button class="glass-button" :label="t('common.cancel')" @click="showCreateDialog = false" />
          <Button class="glass-button primary" :loading="predictionStore.loading" :disabled="!createForm.name" :label="t('common.create')" @click="handleCreate" />
        </div>
      </div>
    </Dialog>

    <Dialog v-model:visible="showJoinDialog" :header="t('leagues.joinLeague')" :modal="true" class="glass-card" :pt="{ header: { class: '!bg-transparent !border-b !border-white/5 !text-white !px-6 !py-4' }, content: { class: '!bg-transparent !px-6 !pb-6' } }">
      <div class="space-y-4 pt-2">
        <div><label class="block text-sm font-medium text-white/60 mb-2">{{ t('leagues.inviteCode') }} *</label><InputText v-model="inviteCode" class="glass-input w-full" placeholder="Código de convite" required /></div>
        <div class="flex justify-end gap-3 pt-4">
          <Button class="glass-button" :label="t('common.cancel')" @click="showJoinDialog = false" />
          <Button class="glass-button primary" :loading="predictionStore.loading" :disabled="!inviteCode" :label="t('leagues.joinLeague')" @click="handleJoin" />
        </div>
      </div>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import { usePredictionStore } from '@/stores/predictions'

const { t } = useI18n()
const toast = useToast()
const predictionStore = usePredictionStore()

const showCreateDialog = ref(false)
const showJoinDialog = ref(false)
const inviteCode = ref('')
const createForm = ref({ name: '', description: '' })

async function handleCreate() {
  if (!createForm.value.name) return
  try {
    await predictionStore.createLeague({ name: createForm.value.name, description: createForm.value.description || undefined })
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('leagues.createLeagueSuccess'), life: 3000 })
    showCreateDialog.value = false
    createForm.value = { name: '', description: '' }
  } catch {
    toast.add({ severity: 'error', summary: t('common.error'), detail: predictionStore.error || t('common.error'), life: 5000 })
  }
}

async function handleJoin() {
  if (!inviteCode.value) return
  try {
    await predictionStore.joinLeague(inviteCode.value)
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('leagues.joinLeagueSuccess'), life: 3000 })
    showJoinDialog.value = false
    inviteCode.value = ''
    predictionStore.fetchLeagues()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error'), detail: predictionStore.error || t('common.error'), life: 5000 })
  }
}

function copyInviteCode(code: string) {
  navigator.clipboard.writeText(code)
  toast.add({ severity: 'info', summary: 'Copiado!', detail: 'Código copiado.', life: 2000 })
}

onMounted(() => {
  predictionStore.fetchLeagues()
})
</script>
