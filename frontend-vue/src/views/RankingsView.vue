<template>
  <div class="page-container">
    <h1 class="section-title">{{ t("rankings.title") }}</h1>

    <TabView class="glass-card !rounded-2xl" :pt="{ root: { class: '!bg-transparent' }, nav: { class: '!bg-transparent !border-b !border-white/10' }, panelContainer: { class: '!bg-transparent' } }">
      <TabPanel value="leaderboard" :header="t('rankings.leaderboard')">
        <div class="p-4">
          <div v-if="predictionStore.loading" class="space-y-3">
            <div v-for="i in 5" :key="i" class="h-12 bg-white/5 rounded animate-pulse" />
          </div>

          <div v-else-if="predictionStore.leaderboard.length === 0" class="empty-state !py-12">
            <p class="text-lg">{{ t('rankings.noUsers') }}</p>
          </div>

          <div v-else class="overflow-x-auto">
            <table class="w-full">
              <thead>
                <tr class="border-b border-white/10 text-left">
                  <th class="py-3 px-4 text-xs font-semibold text-white/30 uppercase tracking-wider">{{ t('rankings.rank') }}</th>
                  <th class="py-3 px-4 text-xs font-semibold text-white/30 uppercase tracking-wider">{{ t('rankings.user') }}</th>
                  <th class="py-3 px-4 text-xs font-semibold text-white/30 uppercase tracking-wider text-right">{{ t('rankings.points') }}</th>
                  <th class="py-3 px-4 text-xs font-semibold text-white/30 uppercase tracking-wider text-right">{{ t('rankings.accuracy') }}</th>
                  <th class="py-3 px-4 text-xs font-semibold text-white/30 uppercase tracking-wider text-right">{{ t('rankings.streak') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(entry, idx) in predictionStore.leaderboard" :key="idx" class="border-b border-white/5 hover:bg-white/2 transition-colors">
                  <td class="py-3 px-4"><span class="text-sm font-bold" :class="idx < 3 ? 'text-purple-400' : 'text-white/60'">#{{ idx + 1 }}</span></td>
                  <td class="py-3 px-4 text-sm text-white/80">{{ getEntryField(entry, 'username') || getEntryField(entry, 'user_id') }}</td>
                  <td class="py-3 px-4 text-sm font-semibold text-right" :class="getEntryNum(entry, 'points') > 0 ? 'text-green-400' : 'text-white/60'">{{ getEntryNum(entry, 'points') }}</td>
                  <td class="py-3 px-4 text-sm text-right text-white/60">{{ formatAccuracy(getEntryNum(entry, 'accuracy')) }}</td>
                  <td class="py-3 px-4 text-sm text-right" :class="streakClass(getEntryNum(entry, 'streak'))">{{ getEntryNum(entry, 'streak') }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </TabPanel>

      <TabPanel value="achievements" :header="t('rankings.achievements')">
        <div class="p-4">
          <div v-if="predictionStore.loading" class="grid-3">
            <div v-for="i in 6" :key="i" class="glass-card p-5 animate-pulse">
              <div class="h-10 w-10 bg-white/10 rounded-full mb-3" />
              <div class="h-5 bg-white/10 rounded w-3/4 mb-2" />
              <div class="h-4 bg-white/5 rounded w-full" />
            </div>
          </div>

          <div v-else-if="predictionStore.achievements.length === 0" class="empty-state !py-12">
            <p class="text-lg">{{ t('rankings.noAchievements') }}</p>
          </div>

          <div v-else class="grid-3">
            <div v-for="a in predictionStore.achievements" :key="a.code" class="glass-card p-5" :class="{ 'opacity-50': !a.unlocked_at }">
              <div class="flex items-start gap-3">
                <div class="w-12 h-12 rounded-xl flex items-center justify-center text-2xl flex-shrink-0" :class="a.unlocked_at ? 'bg-purple-500/20' : 'bg-white/5'">{{ a.icon }}</div>
                <div>
                  <h4 class="font-semibold text-white/80">{{ a.name }}</h4>
                  <p class="text-sm text-white/50 mt-1">{{ a.description }}</p>
                </div>
              </div>
              <div class="mt-3 pt-3 border-t border-white/5">
                <span v-if="a.unlocked_at" class="badge badge-green text-xs">{{ t('rankings.unlocked') }}</span>
                <span v-else class="badge badge-red text-xs">{{ t('rankings.locked') }}</span>
              </div>
            </div>
          </div>
        </div>
      </TabPanel>
    </TabView>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import { usePredictionStore } from '@/stores/predictions'

const { t } = useI18n()
const predictionStore = usePredictionStore()

function getEntryField(entry: Record<string, unknown>, field: string): string {
  return (entry[field] as string) || ''
}

function getEntryNum(entry: Record<string, unknown>, field: string): number {
  return Number(entry[field]) || 0
}

function formatAccuracy(val: number): string {
  return val ? val.toFixed(1) + '%' : '-'
}

function streakClass(val: number): string {
  return val > 0 ? 'text-green-400' : val < 0 ? 'text-red-400' : 'text-white/60'
}

onMounted(() => {
  predictionStore.fetchAchievements()
})
</script>
