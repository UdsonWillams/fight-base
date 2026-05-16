<template>
  <div class="page-container">
    <button class="btn-icon mb-6" @click="$router.push('/events')">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" /></svg>
      <span class="ml-2 text-sm">{{ t('common.back') }}</span>
    </button>

    <div v-if="!authStore.isLoggedIn" class="glass-card p-8 text-center max-w-lg mx-auto">
      <div class="text-4xl mb-4">🔒</div>
      <h2 class="text-xl font-semibold text-white mb-2">Login necessario</h2>
      <p class="text-white/50 mb-6">Voce precisa estar logado para ver os detalhes do evento.</p>
      <div class="flex gap-3 justify-center">
        <router-link to="/login" class="glass-button primary !px-6 !py-2 !rounded-xl">Entrar</router-link>
        <router-link to="/register" class="glass-button !px-6 !py-2 !rounded-xl">Criar Conta</router-link>
      </div>
    </div>

    <div v-else-if="eventStore.loading" class="space-y-4">
      <div class="h-10 bg-white/10 rounded w-64 animate-pulse" />
      <div v-for="i in 4" :key="i" class="glass-card p-6 animate-pulse"><div class="h-8 bg-white/10 rounded w-full mb-4" /></div>
    </div>

    <template v-else-if="event">
      <div class="glass-card p-6 mb-8">
        <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div class="flex-1">
            <h1 class="text-3xl font-black text-white">{{ event.name }}</h1>
            <div class="flex flex-wrap items-center gap-3 mt-3">
              <span class="badge" :class="statusBadgeClass">{{ statusLabel }}</span>
              <span v-if="event.organization" class="badge badge-purple">{{ event.organization }}</span>
            </div>
            <div class="flex flex-wrap gap-4 mt-3 text-sm text-white/50">
              <span class="flex items-center gap-1"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-white/30"><rect x="3" y="4" width="18" height="18" rx="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" /></svg>{{ formattedDate }}</span>
              <span v-if="event.location" class="flex items-center gap-1"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-white/30"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" /></svg>{{ event.location }}</span>
              <span v-if="event.fights" class="flex items-center gap-1"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-white/30"><circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" /></svg>{{ event.fights.length }} lutas</span>
            </div>
          </div>
          <div v-if="authStore.isLoggedIn" class="flex gap-2">
            <button class="glass-button text-sm !py-1.5 !px-4" @click="$router.push(`/events/${event.id}/edit`)">{{ t('events.editEvent') }}</button>
            <button class="glass-button primary text-sm !py-1.5 !px-4" :disabled="eventStore.loading" @click="confirmSimulate">{{ t('events.simulateEvent') }}</button>
            <button class="glass-button danger text-sm !py-1.5 !px-4" @click="confirmDelete">{{ t('common.delete') }}</button>
          </div>
        </div>
      </div>

      <h2 class="text-2xl font-bold text-white/80 mb-6">{{ t('events.fightCard') }}</h2>

      <div v-if="!event.fights || event.fights.length === 0" class="empty-state !py-12">
        <p class="text-lg">{{ t('events.noFights') }}</p>
      </div>

      <div v-else class="space-y-3">
        <div v-if="loadingFighters" class="grid gap-3">
          <div v-for="i in Math.min(event.fights.length, 6)" :key="i" class="glass-card p-6 animate-pulse">
            <div class="flex items-center justify-between gap-4">
              <div class="flex-1"><div class="h-5 bg-white/10 rounded w-32 mb-2" /><div class="h-4 bg-white/10 rounded w-12" /></div>
              <div class="text-center"><div class="h-4 bg-white/10 rounded w-8 mb-2" /><div class="h-3 bg-white/10 rounded w-16" /></div>
              <div class="flex-1 text-right"><div class="h-5 bg-white/10 rounded w-32 mb-2 ml-auto" /><div class="h-4 bg-white/10 rounded w-12 ml-auto" /></div>
            </div>
          </div>
        </div>

        <FightCard
          v-for="fight in sortedFights"
          :key="fight.id"
          :fight="fight"
          :fighter1-name="fight.fighter1?.name || 'TBD'"
          :fighter2-name="fight.fighter2?.name || 'TBD'"
          :fighter1-nickname="fight.fighter1?.nickname"
          :fighter2-nickname="fight.fighter2?.nickname"
          :fighter1-overall="fight.fighter1?.overall_rating || 0"
          :fighter2-overall="fight.fighter2?.overall_rating || 0"
          :fighter1-probability="fight.fighter1_probability"
          :fighter2-probability="fight.fighter2_probability"
        />
      </div>
    </template>

    <div v-else class="empty-state"><p class="text-lg">Evento nao encontrado.</p></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import FightCard from '@/components/events/FightCard.vue'
import { useAuthStore } from '@/stores/auth'
import { useEventStore } from '@/stores/events'
import { api } from '@/services/api'
import type { Fight } from '@/types'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const toast = useToast()
const confirm = useConfirm()
const authStore = useAuthStore()
const eventStore = useEventStore()

const event = computed(() => eventStore.currentEvent)
const loadingFighters = ref(false)

const formattedDate = computed(() => {
  if (!event.value?.date) return 'Data nao definida'
  try { return new Date(event.value.date).toLocaleDateString('pt-BR', { day: 'numeric', month: 'long', year: 'numeric' }) }
  catch { return event.value.date }
})

const statusLabel = computed(() => {
  const map: Record<string, string> = { upcoming: 'Em breve', completed: 'Finalizado', in_progress: 'Em andamento', cancelled: 'Cancelado' }
  return event.value ? (map[event.value.status] || event.value.status) : ''
})

const statusBadgeClass = computed(() => {
  const map: Record<string, string> = { upcoming: 'badge-blue', completed: 'badge-green', in_progress: 'badge-yellow', cancelled: 'badge-red' }
  return event.value ? (map[event.value.status] || 'badge-purple') : ''
})

const sortedFights = computed(() => {
  if (!event.value?.fights) return []
  return [...event.value.fights].sort((a, b) => (b.fight_order || 0) - (a.fight_order || 0))
})

async function loadFighterDetails() {
  if (!event.value?.fights?.length) return

  // Se o backend já enviou overall_rating, não precisa buscar
  const needsFetch = event.value.fights.some(
    (f: any) => !f.fighter1?.overall_rating || !f.fighter2?.overall_rating
  )
  if (!needsFetch) return

  loadingFighters.value = true
  const fights = event.value.fights
  const batchSize = 6

  for (let i = 0; i < fights.length; i += batchSize) {
    const batch = fights.slice(i, i + batchSize)
    const fighterIds = new Set<string>()
    batch.forEach((f: any) => {
      if (f.fighter1_id) fighterIds.add(f.fighter1_id)
      if (f.fighter2_id) fighterIds.add(f.fighter2_id)
    })

    try {
      const fighterDetails = await Promise.all(
        Array.from(fighterIds).map(id => api.getFighter(id).catch(() => null))
      )

      const detailsMap = new Map(fighterDetails.filter(Boolean).map((f: any) => [f.id, f]))

      batch.forEach((fight: any) => {
        if (fight.fighter1_id && detailsMap.has(fight.fighter1_id)) {
          const details = detailsMap.get(fight.fighter1_id)
          if (fight.fighter1) {
            fight.fighter1.overall_rating = details?.overall_rating
            fight.fighter1.nickname = details?.nickname
          }
        }
        if (fight.fighter2_id && detailsMap.has(fight.fighter2_id)) {
          const details = detailsMap.get(fight.fighter2_id)
          if (fight.fighter2) {
            fight.fighter2.overall_rating = details?.overall_rating
            fight.fighter2.nickname = details?.nickname
          }
        }
      })
    } catch {
      // Silencioso - mostra sem overall se falhar
    }
  }

  loadingFighters.value = false
}

watch(() => eventStore.currentEvent, (newEvent) => {
  if (newEvent?.fights?.length) {
    loadFighterDetails()
  }
}, { immediate: true })

function confirmSimulate() {
  if (!event.value) return
  confirm.require({
    message: t('events.simulateConfirm'),
    header: t('events.simulateEvent'),
    acceptClass: 'glass-button primary',
    rejectClass: 'glass-button',
    accept: async () => {
      try {
        await eventStore.simulateEvent(event.value!.id)
        toast.add({ severity: 'success', summary: t('common.success'), detail: 'Evento simulado!', life: 3000 })
        // Recarrega os detalhes dos lutadores após simulação
        await loadFighterDetails()
      } catch {
        toast.add({ severity: 'error', summary: t('common.error'), detail: eventStore.error || t('common.error'), life: 5000 })
      }
    },
  })
}

function confirmDelete() {
  if (!event.value) return
  confirm.require({
    message: t('events.deleteConfirm'),
    header: t('events.deleteEvent'),
    acceptClass: 'glass-button danger',
    rejectClass: 'glass-button',
    accept: async () => {
      try {
        await eventStore.deleteEvent(event.value!.id)
        toast.add({ severity: 'success', summary: t('common.success'), detail: 'Evento deletado!', life: 3000 })
        router.push('/events')
      } catch {
        toast.add({ severity: 'error', summary: t('common.error'), detail: eventStore.error || t('common.error'), life: 5000 })
      }
    },
  })
}

onMounted(async () => {
  const id = route.params.id as string
  if (!id) return
  await authStore.checkAuth()
  if (authStore.isLoggedIn) {
    await eventStore.fetchEvent(id)
  }
})
</script>
