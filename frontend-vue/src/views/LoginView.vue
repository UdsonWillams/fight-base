<template>
  <div class="min-h-screen flex items-center justify-center px-4 py-16">
    <div class="w-full max-w-md">
      <div class="glass-card p-8">
        <div class="text-center mb-8">
          <h1 class="text-3xl font-bold text-white mb-2">{{ t('auth.welcomeBack') }}</h1>
          <p class="text-sm text-white/40">Entre para acessar o FightBase</p>
        </div>

        <button class="flex items-center justify-center gap-3 w-full glass-card !p-3 !rounded-xl hover:!bg-white/8 transition-all mb-6 cursor-pointer" @click="showGoogleMaintenance = true">
          <svg width="20" height="20" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          <span class="font-medium text-white/80">{{ t('auth.googleLogin') }}</span>
        </button>

        <Dialog v-model:visible="showGoogleMaintenance" header="Google" :modal="true" class="glass-card" :pt="{ header: { class: '!bg-transparent !border-b !border-white/5 !text-white !px-6 !py-4' }, content: { class: '!bg-transparent !px-6 !pb-6 !pt-2' } }">
          <p class="text-white/70 mb-6">{{ t('auth.googleMaintenance') }}</p>
          <div class="flex justify-end">
            <button class="glass-button" @click="showGoogleMaintenance = false">{{ t('common.understood') }}</button>
          </div>
        </Dialog>

        <div class="flex items-center gap-3 mb-6">
          <hr class="flex-1 border-white/10" />
          <span class="text-xs text-white/30 uppercase">{{ t('auth.orContinueWith') }}</span>
          <hr class="flex-1 border-white/10" />
        </div>

        <LoginForm @success="onSuccess" @switch-to-register="$router.push('/register')" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import Dialog from 'primevue/dialog'
import LoginForm from '@/components/auth/LoginForm.vue'

const router = useRouter()
const { t } = useI18n()
const toast = useToast()

const showGoogleMaintenance = ref(false)

function onSuccess() {
  toast.add({ severity: 'success', summary: 'Sucesso', detail: t('auth.loginSuccess'), life: 3000 })
  router.push('/')
}
</script>
