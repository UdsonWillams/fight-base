<template>
  <div class="page-container">
    <div class="flex items-center justify-between mb-8">
      <h1 class="section-title !mb-0">{{ t('events.title') }}</h1>
      <Button v-if="authStore.isLoggedIn" class="glass-button primary" :label="t('events.createEvent')" @click="$router.push('/events/create')" />
    </div>

    <div v-if="!authStore.isLoggedIn" class="glass-card p-8 text-center max-w-lg mx-auto">
      <div class="text-4xl mb-4">🔒</div>
      <h2 class="text-xl font-semibold text-white mb-2">Login necessario</h2>
      <p class="text-white/50 mb-6">Voce precisa estar logado para acessar os eventos.</p>
      <div class="flex gap-3 justify-center">
        <router-link to="/login" class="glass-button primary !px-6 !py-2 !rounded-xl">Entrar</router-link>
        <router-link to="/register" class="glass-button !px-6 !py-2 !rounded-xl">Criar Conta</router-link>
      </div>
    </div>

    <template v-else>
      <div v-if="eventStore.loading" class="grid-3">
        <SkeletonCard v-for="i in 6" :key="i" type="event" />
      </div>

      <div v-else-if="eventStore.events.length === 0" class="empty-state">
        <div class="empty-state-icon">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" class="mx-auto">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" />
          </svg>
        </div>
        <p class="text-lg">{{ t('events.noEvents') }}</p>
      </div>

      <div v-else class="grid-3">
        <EventCard v-for="event in eventStore.events" :key="event.id" :event="event" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import EventCard from '@/components/events/EventCard.vue'
import SkeletonCard from '@/components/ui/SkeletonCard.vue'
import { useAuthStore } from '@/stores/auth'
import { useEventStore } from '@/stores/events'

const { t } = useI18n()
const authStore = useAuthStore()
const eventStore = useEventStore()

onMounted(() => {
  authStore.checkAuth().then(() => {
    if (authStore.isLoggedIn) {
      eventStore.fetchEvents({})
    }
  })
})
</script>
