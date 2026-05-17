<template>
  <div class="login-form glass-card">
    <h2 class="form-title">{{ t('auth.login') }}</h2>

    <form @submit.prevent="handleSubmit">
      <div class="field">
        <label for="login-email">{{ t('auth.email') }}</label>
        <InputText
          id="login-email"
          v-model="email"
          type="email"
          :placeholder="t('auth.email')"
          class="w-full"
          required
        />
      </div>

      <div class="field">
        <label for="login-password">{{ t('auth.password') }}</label>
        <Password
          id="login-password"
          v-model="password"
          :placeholder="t('auth.password')"
          :feedback="false"
          toggleMask
          class="w-full"
          required
        />
      </div>

      <div v-if="error" class="error-msg">{{ error }}</div>

      <Button
        type="submit"
        :label="t('auth.login')"
        icon="pi pi-sign-in"
        :loading="loading"
        class="submit-btn w-full"
      />
    </form>

    <div class="form-footer">
      <span>{{ t('auth.noAccount') }}</span>
      <button class="link-btn" @click="$emit('switch-to-register')">
        {{ t('auth.registerNow') }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const auth = useAuthStore()

const emit = defineEmits<{
  success: []
  'switch-to-register': []
}>()

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleSubmit() {
  error.value = ''
  loading.value = true

  try {
    await auth.login(email.value, password.value)
    emit('success')
  } catch (e: any) {
    error.value = e.message || 'Falha ao fazer login'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-form {
  padding: 2rem;
  max-width: 420px;
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

:deep(.p-password .p-password-toggle-icon) {
  color: var(--text-secondary);
}

:deep(.p-password .p-password-toggle-icon:hover) {
  color: var(--text-primary);
}

:deep(.p-password .p-password-input) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 10px 16px;
  color: var(--text-primary);
  width: 100%;
}

:deep(.p-password .p-password-input:focus) {
  border-color: rgba(168, 85, 247, 0.5);
  box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.1);
}

:deep(.p-password .p-password-input::placeholder) {
  color: rgba(255, 255, 255, 0.3);
}
</style>
