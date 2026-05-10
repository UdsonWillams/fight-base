import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/services/api'
import type { Event, EventDetail, Fight, FightCreate } from '@/types'

export const useEventStore = defineStore('events', () => {
  const events = ref<Event[]>([])
  const currentEvent = ref<EventDetail | null>(null)
  const total = ref(0)
  const page = ref(1)
  const pages = ref(1)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchEvents(params?: Record<string, string | number | boolean>) {
    loading.value = true
    error.value = null
    try {
      const merged = { order_by: 'date_desc', ...(params || {}) } as Record<string, string | number>
      const res = await api.getEvents(merged)
      events.value = res
      total.value = res.length
      pages.value = 1
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro ao buscar eventos'
      error.value = msg
    } finally {
      loading.value = false
    }
  }

  async function fetchEvent(id: string) {
    loading.value = true
    error.value = null
    try {
      currentEvent.value = await api.getEvent(id)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro ao buscar evento'
      error.value = msg
    } finally {
      loading.value = false
    }
  }

  async function createEvent(data: { name: string; date: string; location?: string; organization?: string; fights?: FightCreate[] }) {
    loading.value = true
    error.value = null
    try {
      const event = await api.createEvent(data)
      events.value.unshift(event)
      return event
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro ao criar evento'
      error.value = msg
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateEvent(id: string, data: Record<string, unknown>) {
    loading.value = true
    error.value = null
    try {
      const updated = await api.updateEvent(id, data)
      const idx = events.value.findIndex((e) => e.id === id)
      if (idx !== -1) events.value[idx] = updated
      if (currentEvent.value?.id === id) currentEvent.value = updated
      return updated
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro ao atualizar evento'
      error.value = msg
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteEvent(id: string) {
    loading.value = true
    error.value = null
    try {
      await api.deleteEvent(id)
      events.value = events.value.filter((e) => e.id !== id)
      if (currentEvent.value?.id === id) currentEvent.value = null
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro ao deletar evento'
      error.value = msg
      throw e
    } finally {
      loading.value = false
    }
  }

  async function addFight(eventId: string, data: FightCreate) {
    loading.value = true
    error.value = null
    try {
      const fight: Fight = await api.addFightToEvent(eventId, data)
      if (currentEvent.value && currentEvent.value.id === eventId) {
        currentEvent.value.fights.push(fight)
      }
      return fight
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro ao adicionar luta'
      error.value = msg
      throw e
    } finally {
      loading.value = false
    }
  }

  async function simulateEvent(eventId: string) {
    loading.value = true
    error.value = null
    try {
      const result = await api.simulateEvent(eventId)
      if (currentEvent.value && currentEvent.value.id === eventId) {
        const updated = await api.getEvent(eventId)
        currentEvent.value = updated
      }
      return result
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro ao simular evento'
      error.value = msg
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    events,
    currentEvent,
    total,
    page,
    pages,
    loading,
    error,
    fetchEvents,
    fetchEvent,
    createEvent,
    updateEvent,
    deleteEvent,
    addFight,
    simulateEvent,
  }
})
