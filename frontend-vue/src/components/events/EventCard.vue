<template>
    <div class="glass-card p-5 cursor-pointer" @click="$router.push(`/events/${event.id}`)">
    <div class="flex items-start justify-between mb-3 gap-3">
      <div class="flex-1 min-w-0">
        <h3 class="text-lg font-bold text-white truncate">{{ event.name }}</h3>
      </div>
      <span
        class="badge flex-shrink-0 ml-2"
        :class="statusClass"
      >
        {{ statusLabel }}
      </span>
    </div>

    <div class="space-y-2 text-sm text-white/50">
      <div class="flex items-center gap-2">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-white/30 flex-shrink-0" style="margin-top: 1px;">
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" />
        </svg>
        <span>{{ formattedDate }}</span>
      </div>

      <div v-if="event.location" class="flex items-center gap-2">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-white/30 flex-shrink-0" style="margin-top: 1px;">
          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
        </svg>
        <span class="truncate">{{ event.location }}</span>
      </div>

      <div v-if="event.organization" class="flex items-center gap-2">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-white/30 flex-shrink-0" style="margin-top: 1px;">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><polyline points="9 22 9 12 15 12 15 22" />
        </svg>
        <span>{{ event.organization }}</span>
      </div>
    </div>

    <div class="mt-4 pt-3 border-t border-white/5 flex items-center justify-between">
      <span class="badge badge-blue text-xs">
        {{ event.fights_count || 0 }} {{ event.fights_count === 1 ? 'luta' : 'lutas' }}
      </span>
      <span class="text-xs text-white/30">{{ formattedDate }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Event } from '@/types'

const props = defineProps<{
  event: Event
}>()

const formattedDate = computed(() => {
  if (!props.event.date) return 'Data não definida'
  try {
    const d = new Date(props.event.date)
    return d.toLocaleDateString('pt-BR', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    })
  } catch {
    return props.event.date
  }
})

const statusLabel = computed(() => {
  const map: Record<string, string> = {
    upcoming: 'Em breve',
    completed: 'Finalizado',
    in_progress: 'Em andamento',
    cancelled: 'Cancelado',
  }
  return map[props.event.status] || props.event.status
})

const statusClass = computed(() => {
  const map: Record<string, string> = {
    upcoming: 'badge-blue',
    completed: 'badge-green',
    in_progress: 'badge-yellow',
    cancelled: 'badge-red',
  }
  return map[props.event.status] || 'badge-purple'
})
</script>
