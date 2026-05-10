<template>
  <div class="glass-card p-5 animate-pulse">
    <div class="flex items-start justify-between mb-3">
      <div class="space-y-2 flex-1">
        <div class="h-5 bg-white/10 rounded w-3/4" />
        <div class="h-4 bg-white/5 rounded w-1/2" />
      </div>
      <div class="h-6 bg-white/10 rounded-full w-20" />
    </div>

    <div class="flex items-center justify-between mb-3">
      <div class="space-y-2">
        <div class="h-8 bg-white/10 rounded w-12" />
        <div class="h-3 bg-white/5 rounded w-16" />
      </div>
      <div class="space-y-2">
        <div class="h-5 bg-white/10 rounded w-16" />
        <div class="h-3 bg-white/5 rounded w-12" />
      </div>
    </div>

    <div class="space-y-1.5">
      <div v-for="i in 3" :key="i" class="flex items-center gap-2">
        <div class="h-3 bg-white/5 rounded w-16" />
        <div class="flex-1 h-1.5 bg-white/5 rounded-full" />
        <div class="h-3 bg-white/5 rounded w-6" />
      </div>
    </div>

    <div class="mt-3 pt-3 border-t border-white/5 flex items-center justify-between">
      <div class="h-5 bg-white/10 rounded-full w-24" />
      <div class="h-5 bg-white/10 rounded-full w-20" />
    </div>
  </div>
</template>
