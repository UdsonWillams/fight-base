<template>
  <div class="page-container">
    <div class="flex items-center justify-between mb-8">
      <div>
        <button class="text-sm text-white/40 hover:text-white/80 mb-2 block" @click="$router.push('/leagues')">
          &larr; {{ t('common.back') }}
        </button>
        <h1 class="section-title !mb-0">{{ league?.name }}</h1>
      </div>
      <div class="flex gap-2" v-if="league">
        <button v-if="league.is_owner" class="glass-button !bg-red-500/20 !border-red-500/40 !text-red-300" @click="confirmDelete">
          {{ t('common.delete') }}
        </button>
        <button v-if="league.is_member && !league.is_owner" class="glass-button" @click="confirmLeave">
          Sair da Liga
        </button>
        <button v-if="!league.is_member" class="glass-button primary" @click="handleJoin">
          Entrar na Liga
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-white/40 text-center py-20">Carregando...</div>

    <div v-else-if="league" class="space-y-6">
      <div class="glass-card p-5">
        <p class="text-white/60" v-if="league.description">{{ league.description }}</p>
        <p class="text-white/30 italic" v-else>Sem descrição</p>
        <div class="flex flex-wrap gap-4 mt-4 text-sm">
          <span class="text-white/40">Dono: <span class="text-white">{{ league.owner_name }}</span></span>
          <span class="text-white/40">Membros: <span class="text-white">{{ league.members_count }}</span></span>
          <span class="text-white/40">Código: <span class="text-purple-400 font-mono cursor-pointer" @click="copyCode">{{ league.invite_code }}</span></span>
        </div>

        <div class="mt-4 p-4 rounded-lg" style="background: rgba(255,255,255,0.03)">
          <div class="flex items-center gap-3 flex-wrap">
            <span class="text-white/40 text-sm">Evento Ativo:</span>
            <span v-if="league.active_event_name" class="text-white font-medium">{{ league.active_event_name }}</span>
            <span v-else class="text-white/20 italic">Nenhum evento selecionado</span>
            <span v-if="eventStatus" class="badge text-xs" :class="eventStatusBadgeClass">{{ eventStatusLabel }}</span>
          </div>
          <div v-if="league.active_event_date" class="text-white/30 text-xs mt-1">
            {{ new Date(league.active_event_date).toLocaleDateString('pt-BR') }} — {{ league.active_event_fights_count }} lutas
          </div>

          <div v-if="league.is_owner" class="mt-3">
            <Dropdown
              v-model="selectedEventId"
              :options="availableEvents"
              optionLabel="label"
              optionValue="id"
              placeholder="Selecionar evento..."
              class="w-full"
              @change="selectEvent"
            />
          </div>
        </div>
      </div>

      <div class="flex gap-1 border-b border-white/5 overflow-x-auto">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          class="px-4 py-2 text-sm transition-colors whitespace-nowrap"
          :class="activeTab === tab.id ? 'text-purple-400 border-b-2 border-purple-400' : 'text-white/40 hover:text-white/70'"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Tab: Palpitar -->
      <div v-if="activeTab === 'predict'" class="glass-card p-5">
        <div v-if="!league.active_event_id" class="text-white/30 text-center py-10">
          A liga não tem um evento ativo. Peça ao dono para selecionar um.
        </div>
        <div v-else-if="fights.length === 0" class="text-white/40 text-center py-10">Carregando lutas...</div>
        <div v-else>
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-white">Palpite para {{ league.active_event_name }}</h3>
            <span v-if="eventStatus === 'completed'" class="text-green-400 text-sm font-medium">
              Total: {{ totalMyPoints }} pts
            </span>
          </div>

          <div v-if="eventStatus === 'scheduled' || eventStatus === 'upcoming'" class="text-white/40 text-xs mb-4">
            Selecione o vencedor de cada luta
          </div>
          <div v-if="eventStatus === 'in_progress'" class="text-yellow-400 text-xs mb-4">
            Evento em andamento — palpites bloqueados. Acompanhe os resultados abaixo.
          </div>
          <div v-if="eventStatus === 'completed'" class="text-green-400 text-xs mb-4">
            Evento finalizado. Confira seus resultados abaixo.
          </div>

          <div v-for="f in fights" :key="f.id" class="py-3 border-b border-white/5">
            <div class="flex items-center gap-3">
              <div class="flex-1 text-right">
                <button
                  v-if="eventStatus === 'scheduled' || eventStatus === 'upcoming'"
                  @click="togglePick(f, f.fighter1_id)"
                  class="px-3 py-2 rounded-lg text-sm transition-all w-full"
                  :class="picks[f.id] === f.fighter1_id ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' : 'bg-white/5 text-white/60 hover:bg-white/10'"
                >
                  {{ f.fighter1?.name || 'Lutador 1' }}
                </button>
                <div v-else class="px-3 py-2 rounded-lg text-sm w-full" :class="getFighterResultClass(f, f.fighter1_id)">
                  {{ f.fighter1?.name || 'Lutador 1' }}
                  <span v-if="f.result_type && f.winner_id === f.fighter1_id" class="ml-1 text-green-400">✓</span>
                </div>
              </div>
              <span class="text-white/20 text-sm font-bold">VS</span>
              <div class="flex-1">
                <button
                  v-if="eventStatus === 'scheduled' || eventStatus === 'upcoming'"
                  @click="togglePick(f, f.fighter2_id)"
                  class="px-3 py-2 rounded-lg text-sm transition-all w-full"
                  :class="picks[f.id] === f.fighter2_id ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' : 'bg-white/5 text-white/60 hover:bg-white/10'"
                >
                  {{ f.fighter2?.name || 'Lutador 2' }}
                </button>
                <div v-else class="px-3 py-2 rounded-lg text-sm w-full" :class="getFighterResultClass(f, f.fighter2_id)">
                  {{ f.fighter2?.name || 'Lutador 2' }}
                  <span v-if="f.result_type && f.winner_id === f.fighter2_id" class="ml-1 text-green-400">✓</span>
                </div>
              </div>
            </div>

            <div v-if="f.result_type && (eventStatus === 'in_progress' || eventStatus === 'completed')" class="mt-2 text-xs">
              <div v-if="f.winner" class="text-white/50">
                Resultado: <span class="text-green-400">{{ f.winner.name }}</span>
                venceu por <span class="text-white/60">{{ f.result_type }}</span>
                <span v-if="f.finish_round"> no R{{ f.finish_round }}</span>
              </div>
              <div v-if="picks[f.id]" class="mt-1">
                <span v-if="isPickCorrect(f)" class="text-green-400">
                  Seu palpite: ✓ Correto (+{{ getFightPoints(f) }} pts)
                </span>
                <span v-else class="text-red-400">
                  Seu palpite: ✗ Errado
                </span>
              </div>
            </div>
          </div>

          <button
            v-if="eventStatus === 'scheduled' || eventStatus === 'upcoming'"
            class="glass-button primary mt-4 w-full"
            :disabled="!hasPicks || submitting"
            @click="submitPicks"
          >
            {{ submitting ? 'Salvando...' : 'Enviar Palpites' }}
          </button>
          <div v-if="submitError" class="text-red-400 text-sm mt-2">{{ submitError }}</div>
          <div v-if="submitOk" class="text-green-400 text-sm mt-2">{{ submitOk }}</div>
        </div>
      </div>

      <!-- Tab: Membros -->
      <div v-if="activeTab === 'members'" class="glass-card p-5">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-white">Membros ({{ members.length }})</h3>
          <InputText v-model="memberSearch" placeholder="Buscar membro..." class="glass-input !w-48 !py-1.5 !text-sm" />
        </div>
        <div v-if="filteredMembers.length === 0" class="text-white/30 text-center py-10">Nenhum membro encontrado</div>
        <div v-else class="space-y-2">
          <div
            v-for="m in filteredMembers"
            :key="m.user_id"
            class="flex items-center gap-4 p-3 rounded-lg hover:bg-white/5 transition-colors"
          >
            <div class="text-2xl w-10 text-center">{{ m.avatar || '👤' }}</div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-white font-medium truncate">{{ m.username }}</span>
                <span v-if="m.is_owner" class="badge badge-yellow text-[0.6rem] !px-1.5 !py-0.5">Dono</span>
              </div>
              <div class="text-white/40 text-xs">
                {{ m.total_points || 0 }} pts
                <span v-if="m.accuracy != null" class="ml-2">{{ m.accuracy }}% acerto</span>
              </div>
            </div>
            <div class="text-right">
              <div class="text-purple-400 font-bold text-lg">{{ m.total_points || 0 }}</div>
              <div class="text-white/30 text-xs">pontos</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab: Ranking -->
      <div v-if="activeTab === 'ranking'" class="glass-card p-5">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-white">Ranking da Liga</h3>
          <button class="text-xs text-white/50 hover:text-white/80" @click="loadLeaderboard">Atualizar</button>
        </div>
        <div v-if="leaderboard.length === 0" class="text-white/30 text-center py-10">Nenhum ranking disponível</div>
        <div v-else class="space-y-1">
          <div
            v-for="(entry, idx) in leaderboard"
            :key="entry.user_id"
            class="flex items-center gap-4 p-3 rounded-lg transition-colors"
            :class="entry.user_id === authStore.user?.id ? 'bg-purple-500/10 border border-purple-500/20' : 'hover:bg-white/5'"
          >
            <div class="w-8 text-center font-bold text-lg">
              <span v-if="idx === 0">🥇</span>
              <span v-else-if="idx === 1">🥈</span>
              <span v-else-if="idx === 2">🥉</span>
              <span v-else class="text-white/30">{{ idx + 1 }}º</span>
            </div>
            <div class="flex-1">
              <div class="flex items-center gap-2">
                <span class="text-white font-medium">{{ entry.username }}</span>
                <span v-if="entry.user_id === league?.owner_id" class="badge badge-yellow text-[0.6rem] !px-1.5 !py-0.5">Dono</span>
                <span v-if="entry.user_id === authStore.user?.id" class="text-purple-400 text-xs">(você)</span>
              </div>
            </div>
            <div class="text-right">
              <div class="text-purple-400 font-bold text-lg">{{ entry.total_points }}</div>
              <div class="text-white/30 text-xs">pts</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab: Conquistas -->
      <div v-if="activeTab === 'achievements'" class="glass-card p-5">
        <div v-if="achievements.length === 0" class="text-white/30 text-center py-10">Nenhuma conquista desbloqueada</div>
        <div v-else class="grid grid-cols-2 gap-3">
          <div v-for="a in achievements" :key="a.code" class="flex items-center gap-3 p-3 rounded-lg" :class="a.unlocked_at ? 'bg-white/5' : 'bg-white/5 opacity-40'">
            <span class="text-2xl">{{ a.icon || '🏆' }}</span>
            <div>
              <div class="text-white text-sm font-medium">{{ a.name }}</div>
              <div class="text-white/40 text-xs">{{ a.description }}</div>
              <div v-if="a.unlocked_at" class="text-green-400 text-xs mt-1">
                {{ new Date(a.unlocked_at).toLocaleDateString('pt-BR') }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab: Histórico -->
      <div v-if="activeTab === 'history'" class="glass-card p-5">
        <h3 class="text-lg font-semibold text-white mb-4">Histórico de Eventos</h3>
        <div v-if="eventHistory.length === 0" class="text-white/30 text-center py-10">
          Nenhum evento no histórico. Acompanhe os eventos da liga aqui.
        </div>
        <div v-else class="space-y-3">
          <div v-for="h in eventHistory" :key="h.event_id" class="p-4 rounded-lg bg-white/5 border border-white/5">
            <div class="flex items-center justify-between mb-2">
              <div>
                <div class="text-white font-medium">{{ h.event_name }}</div>
                <div class="text-white/30 text-xs">{{ h.event_date ? new Date(h.event_date).toLocaleDateString('pt-BR') : '' }}</div>
              </div>
              <span class="badge badge-green text-xs">Finalizado</span>
            </div>
            <div class="flex gap-4 text-xs text-white/40">
              <span>{{ h.fights_count || 0 }} lutas</span>
              <span v-if="h.my_points != null">Seus pontos: <strong class="text-purple-400">{{ h.my_points }}</strong></span>
              <span v-if="h.my_rank != null">Posição: #{{ h.my_rank }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <Dialog v-model:visible="showDeleteDialog" header="Excluir Liga" :modal="true" class="glass-card" :pt="{ header: { class: '!bg-transparent !border-b !border-white/5 !text-white !px-6 !py-4' }, content: { class: '!bg-transparent !px-6 !pb-6' } }">
      <p class="text-white/70 pt-2 mb-6">Tem certeza que deseja excluir a liga <strong class="text-white">{{ league?.name }}</strong>?</p>
      <div class="flex justify-end gap-3">
        <button class="glass-button" @click="showDeleteDialog = false">Cancelar</button>
        <button class="glass-button !bg-red-500/20 !border-red-500/40 !text-red-300" @click="handleDelete">Excluir</button>
      </div>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import InputText from 'primevue/inputtext'
import Dialog from 'primevue/dialog'
import Dropdown from 'primevue/dropdown'
import { useLeagueStore } from '@/stores/league'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/services/api'
import type { LeagueDetail } from '@/types'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const toast = useToast()
const leagueStore = useLeagueStore()
const authStore = useAuthStore()

const loading = ref(true)
const league = ref<LeagueDetail | null>(null)
const fights = ref<any[]>([])
const picks = ref<Record<string, string | null>>({})
const submitting = ref(false)
const submitError = ref('')
const submitOk = ref('')
const showDeleteDialog = ref(false)
const selectedEventId = ref<string | null>(null)
const availableEvents = ref<any[]>([])
const activeTab = ref('predict')
const leaderboard = ref<any[]>([])
const achievements = ref<any[]>([])
const eventStatus = ref<string>('')
const memberSearch = ref('')
const eventHistory = ref<any[]>([])

const tabs = [
  { id: 'predict', label: 'Palpitar' },
  { id: 'members', label: 'Membros' },
  { id: 'ranking', label: 'Ranking' },
  { id: 'achievements', label: 'Conquistas' },
  { id: 'history', label: 'Histórico' },
]

const eventStatusBadgeClass = computed(() => {
  const map: Record<string, string> = {
    scheduled: 'badge-purple',
    upcoming: 'badge-purple',
    in_progress: 'badge-yellow',
    completed: 'badge-green',
    cancelled: 'badge-red',
  }
  return map[eventStatus.value] || 'badge-purple'
})

const eventStatusLabel = computed(() => {
  const map: Record<string, string> = {
    scheduled: 'Agendado',
    upcoming: 'Agendado',
    in_progress: 'Em Andamento',
    completed: 'Finalizado',
    cancelled: 'Cancelado',
  }
  return map[eventStatus.value] || eventStatus.value
})

const hasPicks = computed(() => Object.keys(picks.value).length > 0)

interface MemberEntry {
  user_id: string
  username: string
  total_points: number
  rank: number | null
  is_owner: boolean
  avatar: string
  accuracy: number | null
}

const members = computed<MemberEntry[]>(() => {
  return leaderboard.value.map((entry: any) => ({
    ...entry,
    is_owner: entry.user_id === league.value?.owner_id,
    avatar: '👤',
    accuracy: null,
  }))
})

const filteredMembers = computed(() => {
  if (!memberSearch.value) return members.value
  const q = memberSearch.value.toLowerCase()
  return members.value.filter((m) => m.username.toLowerCase().includes(q))
})

const totalMyPoints = computed(() => {
  if (!fights.value.length) return 0
  let total = 0
  for (const f of fights.value) {
    total += getFightPoints(f)
  }
  return total
})

function getFighterResultClass(fight: any, fighterId: string) {
  if (!fight.result_type) {
    if (picks.value[fight.id] === fighterId) {
      return 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
    }
    return 'bg-white/5 text-white/60'
  }
  if (fight.winner_id === fighterId) {
    return 'bg-green-500/10 text-green-400 border border-green-500/30'
  }
  return 'bg-white/5 text-white/40'
}

function isPickCorrect(fight: any): boolean {
  if (!fight.winner_id || !picks.value[fight.id]) return false
  return picks.value[fight.id] === fight.winner_id
}

function getFightPoints(fight: any): number {
  return isPickCorrect(fight) ? 1 : 0
}

async function loadData() {
  const id = route.params.id as string
  if (!id) return
  loading.value = true
  try {
    league.value = await leagueStore.fetchLeague(id)
    if (league.value.active_event_id) {
      await loadFights(league.value.active_event_id)
      await loadMyPredictions(id)
    }
    if (league.value.is_owner) {
      await loadAvailableEvents()
    }
    await loadLeaderboard()
    await loadAchievements()
    await loadEventHistory(id)
  } catch {
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Liga não encontrada', life: 3000 })
  } finally {
    loading.value = false
  }
}

async function loadFights(eventId: string) {
  try {
    const event = await api.getEvent(eventId)
    fights.value = event.fights || []
    eventStatus.value = event.status || ''
  } catch { /* ignore */ }
}

async function loadAvailableEvents() {
  try {
    const events = await api.getEvents({ order_by: 'date_desc' } as any)
    availableEvents.value = (events || []).map((e: any) => ({
      id: e.id,
      label: `${e.name} (${new Date(e.date).toLocaleDateString('pt-BR')})`,
    }))
  } catch { /* ignore */ }
}

async function loadMyPredictions(leagueId: string) {
  try {
    const preds = await api.getMyLeaguePredictions(leagueId)
    const newPicks: Record<string, string | null> = {}
    for (const p of preds) {
      if (p.predicted_winner_id) {
        newPicks[p.fight_id] = p.predicted_winner_id
      }
    }
    picks.value = newPicks
  } catch { /* ignore */ }
}

function togglePick(fight: any, fighterId: string) {
  const current = { ...picks.value }
  if (current[fight.id] === fighterId) {
    delete current[fight.id]
  } else {
    current[fight.id] = fighterId
  }
  picks.value = current
}

async function submitPicks() {
  if (!league.value) return
  submitError.value = ''
  submitOk.value = ''
  submitting.value = true
  try {
    const preds = Object.entries(picks.value).map(([fight_id, predicted_winner_id]) => ({
      fight_id,
      predicted_winner_id: predicted_winner_id || null,
    }))
    await leagueStore.submitPredictions(league.value.id, preds)
    submitOk.value = 'Palpites salvos!'
    toast.add({ severity: 'success', summary: 'OK', detail: 'Palpites salvos!', life: 2000 })
  } catch (e: any) {
    submitError.value = e.message || 'Erro'
  } finally {
    submitting.value = false
  }
}

async function loadLeaderboard() {
  if (!league.value) return
  try {
    leaderboard.value = await api.getLeagueLeaderboard(league.value.id)
  } catch { /* ignore */ }
}

const hardcodedAchievements = [
  { code: 'FIRST_PREDICTION', name: 'Primeiro Palpite', description: 'Faça seu primeiro palpite', icon: '📌', category: 'milestone' },
  { code: 'PREDICTIONS_10', name: 'Novato', description: 'Complete 10 palpites', icon: '🥉', category: 'milestone' },
  { code: 'PREDICTIONS_50', name: 'Apostador', description: 'Complete 50 palpites', icon: '🥈', category: 'milestone' },
  { code: 'PREDICTIONS_100', name: 'Veterano', description: 'Complete 100 palpites', icon: '🥇', category: 'milestone' },
  { code: 'STREAK_5', name: 'Em Chamas', description: '5 acertos consecutivos', icon: '🔥', category: 'streak' },
  { code: 'STREAK_10', name: 'Invencível', description: '10 acertos consecutivos', icon: '⚡', category: 'streak' },
  { code: 'UNDERDOG_HUNTER', name: 'Caçador de Underdogs', description: 'Acerte 5 underdogs', icon: '🎯', category: 'special' },
  { code: 'SUBMISSION_MASTER', name: 'Mestre das Subs', description: 'Acerte 10 submissões', icon: '🥋', category: 'accuracy' },
  { code: 'KO_PROPHET', name: 'Profeta do KO', description: 'Acerte 10 KOs', icon: '🥊', category: 'accuracy' },
  { code: 'PERFECT_EVENT', name: 'Evento Perfeito', description: 'Acerte todas as lutas de um evento', icon: '🌟', category: 'special' },
]

async function loadAchievements() {
  try {
    const unlocked = await api.getAchievements()
    const merged = hardcodedAchievements.map((def: any) => {
      const found = unlocked.find((u: any) => u.code === def.code)
      return { ...def, unlocked_at: found?.unlocked_at || null }
    })
    achievements.value = merged
  } catch { /* ignore */ }
}

async function loadEventHistory(leagueId: string) {
  try {
    if (league.value?.active_event_id && eventStatus.value === 'completed') {
      const myPreds = await api.getMyLeaguePredictions(leagueId).catch(() => [])
      const correctCount = myPreds.filter((p: any) => p.is_correct).length
      eventHistory.value = [{
        event_id: league.value.active_event_id,
        event_name: league.value.active_event_name || 'Evento',
        event_date: league.value.active_event_date,
        fights_count: league.value.active_event_fights_count,
        my_points: correctCount,
        my_rank: null,
      }]
    }
  } catch {
    eventHistory.value = []
  }
}

async function selectEvent() {
  if (!league.value || !selectedEventId.value) return
  try {
    await leagueStore.selectEvent(league.value.id, selectedEventId.value)
    toast.add({ severity: 'success', summary: 'OK', detail: 'Evento selecionado!', life: 2000 })
    await loadData()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: 'Erro', detail: e.message || 'Erro', life: 3000 })
  }
}

function handleJoin() {
  if (!league.value) return
  copyCode()
  toast.add({ severity: 'info', summary: 'Código', detail: 'Use o código para entrar via tela de Ligas', life: 4000 })
}

function copyCode() {
  if (!league.value) return
  navigator.clipboard.writeText(league.value.invite_code)
  toast.add({ severity: 'info', summary: 'Copiado', detail: 'Código copiado!', life: 2000 })
}

function confirmDelete() {
  showDeleteDialog.value = true
}

async function handleDelete() {
  if (!league.value) return
  try {
    await leagueStore.deleteLeague(league.value.id)
    toast.add({ severity: 'success', summary: 'OK', detail: 'Liga deletada!', life: 2000 })
    router.push('/leagues')
  } catch (e: any) {
    toast.add({ severity: 'error', summary: 'Erro', detail: e.message || 'Erro', life: 3000 })
  }
}

function confirmLeave() {
  if (!league.value) return
  leagueStore.leaveLeague(league.value.id).then(() => {
    toast.add({ severity: 'success', summary: 'OK', detail: 'Você saiu da liga', life: 2000 })
    router.push('/leagues')
  }).catch((e: any) => {
    toast.add({ severity: 'error', summary: 'Erro', detail: e.message || 'Erro', life: 3000 })
  })
}

watch(() => route.params.id, () => {
  if (route.name === 'league-detail') loadData()
})

onMounted(loadData)
</script>
