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
      <!-- Info Card -->
      <div class="glass-card p-5">
        <p class="text-white/60" v-if="league.description">{{ league.description }}</p>
        <p class="text-white/30 italic" v-else>Sem descrição</p>
        <div class="flex flex-wrap gap-4 mt-4 text-sm">
          <span class="text-white/40">Dono: <span class="text-white">{{ league.owner_name }}</span></span>
          <span class="text-white/40">Membros: <span class="text-white">{{ league.members_count }}</span></span>
          <span class="text-white/40">Código: <span class="text-purple-400 font-mono cursor-pointer" @click="copyCode">{{ league.invite_code }}</span></span>
        </div>

        <!-- Active Event (owner can select) -->
        <div class="mt-4 p-4 rounded-lg" style="background: rgba(255,255,255,0.03)">
          <div class="flex items-center gap-3">
            <span class="text-white/40 text-sm">Evento Ativo:</span>
            <span v-if="league.active_event_name" class="text-white font-medium">{{ league.active_event_name }}</span>
            <span v-else class="text-white/20 italic">Nenhum evento selecionado</span>
          </div>
          <div v-if="league.active_event_date" class="text-white/30 text-xs mt-1">
            {{ new Date(league.active_event_date).toLocaleDateString('pt-BR') }} — {{ league.active_event_fights_count }} lutas
          </div>

          <div v-if="league.is_owner" class="mt-3">
            <select v-model="selectedEventId" class="glass-input text-sm" @change="selectEvent">
              <option value="">Selecionar evento...</option>
              <option v-for="ev in availableEvents" :key="ev.id" :value="ev.id">{{ ev.name }} ({{ ev.status }})</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="flex gap-1 border-b border-white/5">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          class="px-4 py-2 text-sm transition-colors"
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
        <div v-else-if="!fights.length" class="text-white/40 text-center py-10">Carregando lutas...</div>
        <div v-else>
          <h3 class="text-lg font-semibold text-white mb-4">Palpite para {{ league.active_event_name }}</h3>
          <div v-for="f in fights" :key="f.id" class="flex items-center gap-3 py-3 border-b border-white/5">
            <div class="flex-1 text-right">
              <button
                @click="togglePick(f, f.fighter1_id)"
                class="px-3 py-2 rounded-lg text-sm transition-all w-full"
                :class="picks[f.id] === f.fighter1_id ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' : 'bg-white/5 text-white/60 hover:bg-white/10'"
              >
                {{ getFighterName(f.fighter1) || 'Lutador 1' }}
              </button>
            </div>
            <span class="text-white/20 text-sm font-bold">VS</span>
            <div class="flex-1">
              <button
                @click="togglePick(f, f.fighter2_id)"
                class="px-3 py-2 rounded-lg text-sm transition-all w-full"
                :class="picks[f.id] === f.fighter2_id ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' : 'bg-white/5 text-white/60 hover:bg-white/10'"
              >
                {{ getFighterName(f.fighter2) || 'Lutador 2' }}
              </button>
            </div>
          </div>
          <button
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

      <!-- Tab: Leaderboard -->
      <div v-if="activeTab === 'leaderboard'" class="glass-card p-5">
        <button class="text-xs text-white/50 hover:text-white/80 mb-3" @click="loadLeaderboard">Atualizar</button>
        <div v-if="!leaderboard.length" class="text-white/30 text-center py-10">Nenhum ranking disponível</div>
        <table v-else class="w-full text-sm">
          <thead>
            <tr class="text-white/40 text-left border-b border-white/5">
              <th class="pb-2 w-12">#</th>
              <th class="pb-2">Usuário</th>
              <th class="pb-2 text-right">Pontos</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="entry in leaderboard" :key="entry.user_id" class="border-b border-white/5">
              <td class="py-2 text-white/60">{{ entry.rank }}</td>
              <td class="py-2 text-white">{{ entry.username }}</td>
              <td class="py-2 text-right">
                <span class="text-purple-400 font-semibold">{{ entry.total_points }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Tab: Criar Lutador -->
      <div v-if="activeTab === 'createFighter'" class="glass-card p-5">
        <p class="text-white/50 text-sm mb-4">Gaste seus pontos da liga para criar um lutador personalizado.</p>
        <div class="grid grid-cols-2 gap-3 max-w-lg">
          <div><label class="block text-sm text-white/60 mb-1">Nome *</label><input v-model="fighterForm.name" class="glass-input w-full" /></div>
          <div><label class="block text-sm text-white/60 mb-1">Apelido</label><input v-model="fighterForm.nickname" class="glass-input w-full" /></div>
          <div><label class="block text-sm text-white/60 mb-1">Categoria</label><input v-model="fighterForm.actual_weight_class" class="glass-input w-full" placeholder="Ex: Lightweight" /></div>
          <div><label class="block text-sm text-white/60 mb-1">Estilo</label><input v-model="fighterForm.fighting_style" class="glass-input w-full" placeholder="Ex: Striker" /></div>
          <div><label class="block text-sm text-white/60 mb-1">Custo (pontos)</label><input v-model.number="fighterForm.points_cost" type="number" class="glass-input w-full" min="0" /></div>
        </div>
        <button
          class="glass-button primary mt-4"
          :disabled="!fighterForm.name || creatingFighter"
          @click="createFighter"
        >
          {{ creatingFighter ? 'Criando...' : 'Criar Lutador' }}
        </button>
        <div v-if="fighterError" class="text-red-400 text-sm mt-2">{{ fighterError }}</div>
        <div v-if="fighterOk" class="text-green-400 text-sm mt-2">{{ fighterOk }}</div>
      </div>
    </div>

    <!-- Delete Confirm Dialog -->
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
import Dialog from 'primevue/dialog'
import { useLeagueStore } from '@/stores/league'
import { api } from '@/services/api'
import type { LeagueDetail, Fight } from '@/types'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const toast = useToast()
const leagueStore = useLeagueStore()

const loading = ref(true)
const league = ref<LeagueDetail | null>(null)
const fights = ref<any[]>([])
const picks = ref<Record<string, string | null>>({})
const submitting = ref(false)
const submitError = ref('')
const submitOk = ref('')
const showDeleteDialog = ref(false)
const selectedEventId = ref('')
const availableEvents = ref<any[]>([])
const activeTab = ref('predict')
const leaderboard = ref<any[]>([])
const creatingFighter = ref(false)
const fighterError = ref('')
const fighterOk = ref('')
const fighterForm = ref({ name: '', nickname: '', actual_weight_class: '', fighting_style: '', points_cost: 0 })

const tabs = [
  { id: 'predict', label: 'Palpitar' },
  { id: 'leaderboard', label: 'Ranking' },
  { id: 'createFighter', label: 'Criar Lutador' },
]

const hasPicks = computed(() => Object.keys(picks.value).length > 0)

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
    // Pre-fill picks from saved predictions
  } catch { /* ignore */ }
}

async function loadAvailableEvents() {
  try {
    const events = await api.getEvents({ order_by: 'date_desc' } as any)
    availableEvents.value = events || []
  } catch { /* ignore */ }
}

async function loadMyPredictions(leagueId: string) {
  try {
    const preds = await api.getMyLeaguePredictions(leagueId)
    for (const p of preds) {
      if (p.predicted_winner_id) {
        picks.value[p.fight_id] = p.predicted_winner_id
      }
    }
  } catch { /* ignore */ }
}

function getFighterName(f: any): string {
  return f?.name || ''
}

function togglePick(fight: any, fighterId: string) {
  if (picks.value[fight.id] === fighterId) {
    delete picks.value[fight.id]
  } else {
    picks.value[fight.id] = fighterId
  }
  // Trigger reactivity
  picks.value = { ...picks.value }
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

async function createFighter() {
  if (!league.value) return
  fighterError.value = ''
  fighterOk.value = ''
  creatingFighter.value = true
  try {
    const result = await leagueStore.createFighter(league.value.id, fighterForm.value)
    fighterOk.value = `Lutador "${result.name}" criado! Pontos restantes: ${result.remaining_points}`
    fighterForm.value = { name: '', nickname: '', actual_weight_class: '', fighting_style: '', points_cost: 0 }
    toast.add({ severity: 'success', summary: 'Lutador criado!', detail: result.name, life: 3000 })
  } catch (e: any) {
    fighterError.value = e.message || 'Erro'
  } finally {
    creatingFighter.value = false
  }
}

watch(() => route.params.id, () => {
  if (route.name === 'league-detail') loadData()
})

onMounted(loadData)
</script>
