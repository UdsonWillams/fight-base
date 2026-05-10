<template>
  <div class="register-form glass-card">
    <h2 class="form-title">{{ t('auth.register') }}</h2>

    <form @submit.prevent="handleSubmit">
      <div class="field">
        <label for="reg-username">{{ t('auth.username') }}</label>
        <InputText
          id="reg-username"
          v-model="username"
          :placeholder="t('auth.username')"
          class="w-full"
          required
        />
      </div>

      <div class="field">
        <label for="reg-email">{{ t('auth.email') }}</label>
        <InputText
          id="reg-email"
          v-model="email"
          type="email"
          :placeholder="t('auth.email')"
          class="w-full"
          required
        />
      </div>

      <div class="field">
        <label for="reg-password">{{ t('auth.password') }}</label>
        <Password
          id="reg-password"
          v-model="password"
          :placeholder="t('auth.password')"
          toggleMask
          class="w-full"
          required
          @input="checkStrength"
        />
        <div v-if="password" class="strength-bar">
          <div class="strength-segments">
            <div v-for="i in 4" :key="i" class="strength-segment" :class="{ active: i <= strengthLevel }" />
          </div>
          <span class="strength-label">{{ strengthLabel }}</span>
        </div>
      </div>

      <div class="field">
        <label for="reg-confirm">{{ t('auth.confirmPassword') }}</label>
        <Password
          id="reg-confirm"
          v-model="confirmPassword"
          :placeholder="t('auth.confirmPassword')"
          :feedback="false"
          toggleMask
          class="w-full"
          required
        />
        <span v-if="confirmPassword && password !== confirmPassword" class="match-error">
          Senhas não conferem
        </span>
      </div>

      <div class="field">
        <label for="reg-birth">{{ t('auth.birthDate') }}</label>
        <DatePicker
          id="reg-birth"
          v-model="birthDate"
          :placeholder="t('auth.birthDate')"
          class="w-full"
          showIcon
          dateFormat="dd/mm/yy"
        />
      </div>

      <div class="field">
        <label>{{ t('auth.avatar') }}</label>
        <div class="avatar-grid">
          <button
            v-for="emoji in avatars"
            :key="emoji"
            type="button"
            class="avatar-btn"
            :class="{ selected: selectedAvatar === emoji }"
            @click="selectedAvatar = emoji"
          >
            {{ emoji }}
          </button>
        </div>
      </div>

      <div v-if="error" class="error-msg">{{ error }}</div>

      <Button
        type="submit"
        :label="t('auth.register')"
        icon="pi pi-user-plus"
        :loading="loading"
        class="submit-btn w-full"
      />
    </form>

    <div class="form-footer">
      <span>{{ t('auth.hasAccount') }}</span>
      <button class="link-btn" @click="$emit('switch-to-login')">
        {{ t('auth.loginNow') }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import DatePicker from 'primevue/datepicker'
import Button from 'primevue/button'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const auth = useAuthStore()

const emit = defineEmits<{
  success: []
  'switch-to-login': []
}>()

const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const birthDate = ref<Date | null>(null)
const selectedAvatar = ref('')
const loading = ref(false)
const error = ref('')

const avatars = [
  '\u{1F9B8}', '\u{1F9B8}\u200D\u2642\uFE0F', '\u{1F9B8}\u200D\u2640\uFE0F',
  '\u{1F94B}', '\u{1F3CB}\uFE0F', '\u{1F3CB}\u200D\u2642\uFE0F',
  '\u{1F938}', '\u{1F938}\u200D\u2642\uFE0F', '\u{1F938}\u200D\u2640\uFE0F',
  '\u{1F93C}', '\u{1F93C}\u200D\u2642\uFE0F', '\u{1F93C}\u200D\u2640\uFE0F',
  '\u{1F4AA}', '\u{1F44A}', '\u{1F94A}', '\u{1F525}',
]

const strengthLevel = computed(() => {
  const p = password.value
  let score = 0
  if (p.length >= 6) score++
  if (p.length >= 10) score++
  if (/[A-Z]/.test(p) && /[a-z]/.test(p)) score++
  if (/[0-9]/.test(p) && /[^A-Za-z0-9]/.test(p)) score++
  return Math.min(score, 4)
})

const strengthLabel = computed(() => {
  const labels = [t('auth.weak'), t('auth.fair'), t('auth.strong'), t('auth.veryStrong')]
  return labels[strengthLevel.value - 1] || ''
})

function checkStrength() {
  // reactive computed handles it
}

async function handleSubmit() {
  error.value = ''

  if (password.value !== confirmPassword.value) {
    error.value = 'Senhas não conferem'
    return
  }

  loading.value = true

  try {
    await auth.register({
      email: email.value,
      password: password.value,
      username: username.value,
    })
    await auth.login(email.value, password.value)
    emit('success')
  } catch (e: any) {
    error.value = e.message || 'Falha ao criar conta'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-form {
  padding: 2rem;
  max-width: 460px;
  margin: 0 auto;
}

.form-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 1.5rem;
  text-align: center;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}

.field label {
  font-size: 0.85rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.w-full {
  width: 100%;
}

.strength-bar {
  margin-top: 8px;
}

.strength-segments {
  display: flex;
  gap: 4px;
  margin-bottom: 4px;
}

.strength-segment {
  flex: 1;
  height: 4px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.06);
  transition: background var(--transition);
}

.strength-segment:nth-child(1).active { background: var(--danger); }
.strength-segment:nth-child(2).active { background: var(--warning); }
.strength-segment:nth-child(3).active { background: var(--primary); }
.strength-segment:nth-child(4).active { background: var(--success); }

.strength-label {
  font-size: 0.7rem;
  color: var(--text-muted);
  text-transform: uppercase;
  font-weight: 600;
}

.match-error {
  font-size: 0.75rem;
  color: var(--danger);
}

.avatar-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 6px;
}

.avatar-btn {
  background: rgba(255, 255, 255, 0.04);
  border: 2px solid transparent;
  border-radius: 10px;
  padding: 8px 4px;
  font-size: 1.3rem;
  cursor: pointer;
  transition: all var(--transition);
  text-align: center;
}

.avatar-btn:hover {
  background: rgba(255, 255, 255, 0.08);
}

.avatar-btn.selected {
  border-color: var(--accent);
  background: rgba(124, 58, 237, 0.15);
}

.submit-btn {
  margin-top: 8px;
}

.error-msg {
  color: var(--danger);
  font-size: 0.85rem;
  padding: 8px 12px;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 8px;
  margin-bottom: 12px;
}

.form-footer {
  text-align: center;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--glass-border);
  font-size: 0.85rem;
  color: var(--text-secondary);
  display: flex;
  justify-content: center;
  gap: 6px;
}

.link-btn {
  background: none;
  border: none;
  color: var(--accent-light);
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
}

.link-btn:hover {
  text-decoration: underline;
}
</style>
