<template>
  <div class="page-container">
    <button class="btn-icon mb-6" @click="$router.back()">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" /></svg>
      <span class="ml-2 text-sm">{{ t('common.back') }}</span>
    </button>

    <h1 class="section-title">{{ t('events.editEvent') }}</h1>

    <div v-if="eventStore.loading" class="space-y-4">
      <div class="h-10 bg-white/10 rounded w-64 animate-pulse" />
      <div class="glass-card p-6 animate-pulse"><div class="h-8 bg-white/5 rounded w-full mb-4" /><div class="h-8 bg-white/5 rounded w-full" /></div>
    </div>

    <template v-else-if="event">
      <div class="glass-card p-6 mb-8">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label class="block text-sm font-medium text-white/60 mb-2">{{ t('events.name') }} *</label>
            <InputText v-model="form.name" class="glass-input w-full" required />
          </div>
          <div>
            <label class="block text-sm font-medium text-white/60 mb-2">{{ t('events.date') }} *</label>
            <DatePicker v-model="form.date" class="w-full" input-class="glass-input w-full" show-icon />
          </div>
          <div>
            <label class="block text-sm font-medium text-white/60 mb-2">{{ t('events.location') }}</label>
            <InputText v-model="form.location" class="glass-input w-full" />
          </div>
          <div>
            <label class="block text-sm font-medium text-white/60 mb-2">{{ t('events.organization') }}</label>
            <Select v-model="form.organization" :options="organizations" option-label="label" option-value="value" class="w-full" panel-class="!bg-gray-900 !border-white/10" />
          </div>
        </div>
      </div>

      <div class="glass-card p-6 mb-8">
        <FightCardBuilder v-model="fights" :event-id="event.id" />
      </div>

      <div class="flex justify-end gap-3">
        <Button class="glass-button danger !py-3 !px-8 !text-base" :label="t('events.deleteEvent')" @click="confirmDelete" />
        <Button class="glass-button primary !py-3 !px-8 !text-base" :loading="eventStore.loading" :disabled="!form.name || !form.date" :label="t('common.save')" @click="handleSubmit" />
      </div>
    </template>

    <div v-else class="empty-state"><p class="text-lg">Evento não encontrado.</p></div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import InputText from 'primevue/inputtext'
import DatePicker from 'primevue/datepicker'
import Select from 'primevue/select'
import Button from 'primevue/button'
import FightCardBuilder from '@/components/events/FightCardBuilder.vue'
import { useEventStore } from '@/stores/events'
import type { FightCreate } from '@/types'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const toast = useToast()
const confirm = useConfirm()
const eventStore = useEventStore()

const event = ref(eventStore.currentEvent)
const form = ref({ name: '', date: null as Date | null, location: '', organization: '' })
const fights = ref<FightCreate[]>([])

const organizations = [
  { label: 'UFC', value: 'UFC' },
  { label: 'Bellator', value: 'Bellator' },
  { label: 'ONE Championship', value: 'ONE Championship' },
  { label: 'PFL', value: 'PFL' },
]

watch(() => eventStore.currentEvent, (e) => {
  if (e) {
    event.value = e
    form.value = { name: e.name || '', date: e.date ? new Date(e.date) : null, location: e.location || '', organization: e.organization || '' }
    fights.value = (e.fights || []).map((f, i) => ({
      fighter1_id: f.fighter1_id,
      fighter2_id: f.fighter2_id,
      position: f.fight_type,
      fight_order: i + 1,
    }))
  }
})

async function handleSubmit() {
  if (!event.value || !form.value.name || !form.value.date) return
  try {
    await eventStore.updateEvent(event.value.id, {
      name: form.value.name,
      date: form.value.date.toISOString(),
      location: form.value.location || undefined,
      organization: form.value.organization || undefined,
      fights: fights.value,
    })
    toast.add({ severity: 'success', summary: t('common.success'), detail: 'Evento atualizado!', life: 3000 })
    router.push(`/events/${event.value.id}`)
  } catch {
    toast.add({ severity: 'error', summary: t('common.error'), detail: eventStore.error || t('common.error'), life: 5000 })
  }
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

onMounted(() => {
  const id = route.params.id as string
  if (id) eventStore.fetchEvent(id)
})
</script>
