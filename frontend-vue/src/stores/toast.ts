import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ToastSeverity = 'success' | 'info' | 'warn' | 'error'

export interface ToastMessage {
  severity: ToastSeverity
  summary: string
  detail: string
  life: number
}

export const useToastStore = defineStore('toast', () => {
  const messages = ref<ToastMessage[]>([])

  function add(message: ToastMessage) {
    messages.value.push(message)
  }

  function remove(message: ToastMessage) {
    const idx = messages.value.indexOf(message)
    if (idx > -1) messages.value.splice(idx, 1)
  }

  function show(severity: ToastSeverity, summary: string, detail: string = '', life: number = 3000) {
    add({ severity, summary, detail, life })
  }

  function showSuccess(summary: string, detail?: string) {
    show('success', summary, detail || '')
  }

  function showError(summary: string, detail?: string) {
    show('error', summary, detail || '')
  }

  function showInfo(summary: string, detail?: string) {
    show('info', summary, detail || '')
  }

  function showWarn(summary: string, detail?: string) {
    show('warn', summary, detail || '')
  }

  return { messages, add, remove, show, showSuccess, showError, showInfo, showWarn }
})
