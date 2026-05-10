import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import PrimeVue from 'primevue/config'
import Aura from '@primeuix/themes/aura'
import ConfirmationService from 'primevue/confirmationservice'
import ToastService from 'primevue/toastservice'
import ptBR from './locales/pt-BR.json'
import enUS from './locales/en-US.json'
import router from './router'
import App from './App.vue'
import './assets/css/theme.css'

const savedLocale = localStorage.getItem('locale') || 'pt-BR'

const i18n = createI18n({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'pt-BR',
  messages: {
    'pt-BR': ptBR,
    'en-US': enUS,
  },
})

const pinia = createPinia()

const app = createApp(App)

app.use(pinia)
app.use(router)
app.use(i18n)
app.use(PrimeVue, {
  theme: {
    preset: Aura,
    options: {
      darkModeSelector: '.app-dark',
    },
  },
})
app.use(ConfirmationService)
app.use(ToastService)

app.mount('#app')
