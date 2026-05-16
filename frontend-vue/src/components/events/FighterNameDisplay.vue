<template>
  <span class="fighter-name-display">
    <template v-if="nickname && name">
      <span class="first-name">{{ firstName }}</span>
      <span v-if="firstName" class="space">&nbsp;</span>
      <span class="nickname">"{{ nickname }}"</span>
      <span v-if="lastNames" class="space">&nbsp;</span>
      <span class="last-names">{{ lastNames }}</span>
    </template>
    <template v-else>
      {{ name }}
    </template>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  name: string
  nickname?: string | null
}>()

const firstName = computed(() => {
  if (!props.name) return ''
  const parts = props.name.trim().split(' ')
  return parts[0] || ''
})

const lastNames = computed(() => {
  if (!props.name) return ''
  const parts = props.name.trim().split(' ')
  return parts.slice(1).join(' ') || ''
})
</script>

<style scoped>
.fighter-name-display {
  display: inline;
  line-height: 1.3;
}

.first-name,
.last-names {
  color: inherit;
  font-weight: inherit;
}

.nickname {
  color: var(--accent-light);
  font-style: italic;
  font-weight: 500;
}

.space {
  display: inline;
}
</style>
