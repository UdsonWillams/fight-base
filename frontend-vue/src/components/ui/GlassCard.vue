<template>
  <div
    class="glass-card"
    :class="[hover ? 'hoverable' : '', extraClass]"
    :style="{ padding }"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    padding?: string
    hover?: boolean
    extraClass?: string
  }>(),
  {
    padding: '2rem',
    hover: true,
    extraClass: '',
  },
)
</script>

<style scoped>
.glass-card {
  background: var(--glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--glass-shadow);
  transition: all var(--transition);
}

.glass-card.hoverable:hover {
  background: var(--bg-card-hover);
  border-color: var(--glass-border-hover);
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
}
</style>
