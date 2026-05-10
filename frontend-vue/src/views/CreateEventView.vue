<template>
  <div class="page-container">
    <button class="btn-icon mb-6" @click="$router.back()">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" /></svg>
      <span class="ml-2 text-sm">{{ t('common.back') }}</span>
    </button>

    <h1 class="section-title">{{ t('events.createEvent') }}</h1>

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
      <FightCardBuilder v-model="fights" event-id="new" />
    </div>

    <div class="flex justify-end">
      <Button class="glass-button primary !py-3 !px-8 !text-base" :loading="eventStore.loading" :disabled="!form.name || !form.date" :label="t('common.create')" @click="handleSubmit" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import InputText from 'primevue/inputtext'
import DatePicker from 'primevue/datepicker'
import Select from 'primevue/select'
import Button from 'primevue/button'
import FightCardBuilder from '@/components/events/FightCardBuilder.vue'
import { useEventStore } from '@/stores/events'
import type { FightCreate } from '@/types'

const router = useRouter()
const { t } = useI18n()
const toast = useToast()
const eventStore = useEventStore()

const form = ref({ name: '', date: null as Date | null, location: '', organization: '' })
const fights = ref<FightCreate[]>([])

const organizations = [
  { label: 'UFC', value: 'UFC' },
  { label: 'Bellator', value: 'Bellator' },
  { label: 'ONE Championship', value: 'ONE Championship' },
  { label: 'PFL', value: 'PFL' },
]

async function handleSubmit() {
  if (!form.value.name || !form.value.date) return
  try {
    const event = await eventStore.createEvent({
      name: form.value.name,
      date: form.value.date.toISOString(),
      location: form.value.location || undefined,
      organization: form.value.organization || undefined,
      fights: fights.value.length > 0 ? fights.value : undefined,
    })
    toast.add({ severity: 'success', summary: t('common.success'), detail: 'Evento criado com sucesso!', life: 3000 })
    router.push(`/events/${event.id}`)
  } catch {
    toast.add({ severity: 'error', summary: t('common.error'), detail: eventStore.error || t('common.error'), life: 5000 })
  }
}
</script>
