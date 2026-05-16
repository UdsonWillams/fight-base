<template>
  <div class="page-container">
    <div class="flex items-center justify-between mb-8">
      <h1 class="section-title !mb-0">Admin Dashboard</h1>
      <span class="glass-badge">{{ authStore.user?.role }}</span>
    </div>

    <div class="admin-grid">
      <!-- SECTION 1: Import UFC Dataset -->
      <div class="glass-card p-6">
        <h2 class="text-xl font-semibold text-white mb-1">Importar Dataset UFC</h2>
        <p class="text-white/50 text-sm mb-4">Executa o pipeline completo de importacao (9 etapas)</p>

        <div class="flex gap-3 mb-4">
          <button
            class="glass-button primary"
            :disabled="importTask.status === 'running'"
            @click="startImport"
          >
            {{ importTask.status === 'running' ? 'Importando...' : 'Iniciar Importacao' }}
          </button>
          <button
            v-if="importTask.status === 'running'"
            class="glass-button !bg-red-500/20 !border-red-500/40 !text-red-300 hover:!bg-red-500/30"
            @click="cancelImport"
          >
            Cancelar
          </button>
        </div>

        <div v-if="importTask.taskId && importTask.status !== 'idle'" class="space-y-3">
          <div class="flex items-center justify-between text-sm">
            <span class="text-white/70">{{ importTask.message }}</span>
            <span class="text-white/50">{{ importTask.progress }}%</span>
          </div>
          <div class="progress-bar">
            <div
              class="progress-fill"
              :class="{ 'progress--error': importTask.status === 'error', 'progress--done': importTask.status === 'completed' }"
              :style="{ width: importTask.progress + '%' }"
            />
          </div>
          <div :class="statusBadgeClass(importTask.status)" class="text-xs inline-block px-3 py-1 rounded-full">
            {{ importTask.status }}
          </div>

          <div v-if="importTask.stats" class="mt-3 p-3 rounded-lg" style="background: rgba(255,255,255,0.03)">
            <p class="text-white/70 text-sm mb-2 font-medium">Estatisticas da Importacao:</p>
            <div class="grid grid-cols-2 gap-2 text-sm">
              <span class="text-white/50">Lutadores:</span>
              <span class="text-white">{{ importTask.stats.fighters_created ?? '-' }}</span>
              <span class="text-white/50">Eventos:</span>
              <span class="text-white">{{ importTask.stats.events_created ?? '-' }}</span>
              <span class="text-white/50">Lutas:</span>
              <span class="text-white">{{ importTask.stats.fights_created ?? '-' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- SECTION 2: Train ML Model -->
      <div class="glass-card p-6">
        <h2 class="text-xl font-semibold text-white mb-1">Treinar Modelo ML</h2>
        <p class="text-white/50 text-sm mb-4">Treina o Stacking Ensemble V2 (RF + HGB + LogisticRegression)</p>

        <div class="flex items-center gap-4 mb-4">
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" v-model="trainQuick" class="w-4 h-4 accent-purple-500" />
            <span class="text-white/70 text-sm">Modo Rapido (5 iter, ~10 min)</span>
          </label>
        </div>

        <div class="flex gap-3 mb-4">
          <button
            class="glass-button primary"
            :disabled="trainTask.status === 'running'"
            @click="startTraining"
          >
            {{ trainTask.status === 'running' ? 'Treinando...' : 'Iniciar Treinamento' }}
          </button>
        </div>

        <div v-if="trainTask.taskId && trainTask.status !== 'idle'" class="space-y-3">
          <div class="flex items-center justify-between text-sm">
            <span class="text-white/70">{{ trainTask.message }}</span>
            <span class="text-white/50">{{ trainTask.progress }}%</span>
          </div>
          <div class="progress-bar">
            <div
              class="progress-fill"
              :class="{ 'progress--error': trainTask.status === 'error', 'progress--done': trainTask.status === 'completed' }"
              :style="{ width: trainTask.progress + '%' }"
            />
          </div>
          <div :class="statusBadgeClass(trainTask.status)" class="text-xs inline-block px-3 py-1 rounded-full">
            {{ trainTask.status }}
          </div>

          <div v-if="trainTask.output" class="mt-3">
            <p class="text-white/70 text-sm mb-2 font-medium">Output do Treino:</p>
            <pre class="text-xs text-white/50 p-3 rounded-lg overflow-auto max-h-48" style="background: rgba(0,0,0,0.3)">{{ trainTask.output }}</pre>
          </div>
        </div>
      </div>

      <!-- SECTION 3: Query Task by ID -->
      <div class="glass-card p-6">
        <h2 class="text-xl font-semibold text-white mb-1">Consultar Task</h2>
        <p class="text-white/50 text-sm mb-4">Verifique o status de uma task por ID</p>

        <div class="flex gap-3 mb-4">
          <input
            v-model="queryTaskId"
            type="text"
            placeholder="Cole o task_id aqui..."
            class="glass-input flex-1"
            @keyup.enter="queryTask"
          />
          <button class="glass-button" @click="queryTask">Consultar</button>
        </div>

        <div class="flex gap-2 mb-3">
          <button class="text-xs px-3 py-1 rounded-full border border-white/10 text-white/50 hover:text-white/80 hover:border-white/20" @click="queryType = 'import'">
            Import
          </button>
          <button class="text-xs px-3 py-1 rounded-full border border-white/10 text-white/50 hover:text-white/80 hover:border-white/20" @click="queryType = 'train'">
            Train
          </button>
        </div>

        <div v-if="queryResult" class="space-y-2">
          <div class="flex items-center justify-between text-sm">
            <span class="text-white/70">{{ queryResult.message }}</span>
            <span class="text-white/50">{{ queryResult.progress ?? '-' }}%</span>
          </div>
          <div :class="statusBadgeClass(queryResult.status)" class="text-xs inline-block px-3 py-1 rounded-full">
            {{ queryResult.status }}
          </div>
          <pre v-if="queryResult.output" class="text-xs text-white/50 p-3 rounded-lg overflow-auto max-h-32 mt-2" style="background: rgba(0,0,0,0.3)">{{ queryResult.output }}</pre>
        </div>

        <div v-if="queryError" class="text-red-400 text-sm mt-2">{{ queryError }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onUnmounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/services/api'

const authStore = useAuthStore()

// ── Import Task ──
const importTask = reactive<{
  taskId: string | null
  status: string
  message: string
  progress: number
  stats: Record<string, number> | null
}>({
  taskId: null,
  status: 'idle',
  message: '',
  progress: 0,
  stats: null,
})

let importPollTimer: ReturnType<typeof setInterval> | null = null

async function startImport() {
  try {
    const res = await api.triggerImport()
    importTask.taskId = res.task_id
    importTask.status = 'running'
    importTask.message = res.message
    importTask.progress = 0
    importTask.stats = null
    startImportPolling()
  } catch (e: any) {
    importTask.status = 'error'
    importTask.message = e.message || 'Erro ao iniciar importacao'
  }
}

function startImportPolling() {
  stopImportPolling()
  importPollTimer = setInterval(async () => {
    if (!importTask.taskId || importTask.status === 'completed' || importTask.status === 'error' || importTask.status === 'cancelled' || importTask.status === 'timeout') {
      stopImportPolling()
      return
    }
    try {
      const status = await api.getImportStatus(importTask.taskId)
      importTask.status = status.status
      importTask.message = status.message
      importTask.progress = status.progress ?? importTask.progress
      importTask.stats = status.stats ?? importTask.stats
      if (status.status === 'completed' || status.status === 'error' || status.status === 'timeout' || status.status === 'cancelled') {
        stopImportPolling()
      }
    } catch {
      stopImportPolling()
    }
  }, 3000)
}

function stopImportPolling() {
  if (importPollTimer) {
    clearInterval(importPollTimer)
    importPollTimer = null
  }
}

async function cancelImport() {
  if (!importTask.taskId) return
  try {
    await api.cancelImport(importTask.taskId)
    importTask.status = 'cancelled'
    importTask.message = 'Cancelamento solicitado'
    stopImportPolling()
  } catch (e: any) {
    // ignore
  }
}

// ── Train Task ──
const trainQuick = ref(true)

const trainTask = reactive<{
  taskId: string | null
  status: string
  message: string
  progress: number
  output: string | null
}>({
  taskId: null,
  status: 'idle',
  message: '',
  progress: 0,
  output: null,
})

let trainPollTimer: ReturnType<typeof setInterval> | null = null

async function startTraining() {
  try {
    const res = await api.triggerTraining(trainQuick.value)
    trainTask.taskId = res.task_id
    trainTask.status = 'running'
    trainTask.message = res.message
    trainTask.progress = 0
    trainTask.output = null
    startTrainPolling()
  } catch (e: any) {
    trainTask.status = 'error'
    trainTask.message = e.message || 'Erro ao iniciar treinamento'
  }
}

function startTrainPolling() {
  stopTrainPolling()
  trainPollTimer = setInterval(async () => {
    if (!trainTask.taskId || trainTask.status === 'completed' || trainTask.status === 'error') {
      stopTrainPolling()
      return
    }
    try {
      const status = await api.getTrainingStatus(trainTask.taskId)
      trainTask.status = status.status
      trainTask.message = status.message
      trainTask.progress = status.progress ?? trainTask.progress
      trainTask.output = status.output ?? trainTask.output
      if (status.status === 'completed' || status.status === 'error') {
        stopTrainPolling()
      }
    } catch {
      stopTrainPolling()
    }
  }, 2000)
}

function stopTrainPolling() {
  if (trainPollTimer) {
    clearInterval(trainPollTimer)
    trainPollTimer = null
  }
}

// ── Query Task ──
const queryTaskId = ref('')
const queryType = ref('import')
const queryResult = ref<any>(null)
const queryError = ref('')

async function queryTask() {
  queryError.value = ''
  queryResult.value = null
  if (!queryTaskId.value.trim()) {
    queryError.value = 'Informe um task_id'
    return
  }
  try {
    if (queryType.value === 'import') {
      queryResult.value = await api.getImportStatus(queryTaskId.value.trim())
    } else {
      queryResult.value = await api.getTrainingStatus(queryTaskId.value.trim())
    }
  } catch (e: any) {
    queryError.value = e.message || 'Erro ao consultar task'
  }
}

// ── Helpers ──
function statusBadgeClass(status: string) {
  const map: Record<string, string> = {
    running: 'bg-blue-500/20 text-blue-300 border border-blue-500/30',
    completed: 'bg-green-500/20 text-green-300 border border-green-500/30',
    error: 'bg-red-500/20 text-red-300 border border-red-500/30',
    timeout: 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30',
    cancelled: 'bg-gray-500/20 text-gray-300 border border-gray-500/30',
    not_found: 'bg-gray-500/20 text-gray-400 border border-gray-500/30',
    idle: 'bg-white/5 text-white/50 border border-white/10',
  }
  return map[status] || map.idle
}

onUnmounted(() => {
  stopImportPolling()
  stopTrainPolling()
})
</script>

<style scoped>
.admin-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

@media (max-width: 768px) {
  .admin-grid {
    grid-template-columns: 1fr;
  }
}

.glass-badge {
  background: rgba(124, 58, 237, 0.15);
  border: 1px solid rgba(124, 58, 237, 0.3);
  color: #c4b5fd;
  padding: 4px 14px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.progress-bar {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.06);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 3px;
  background: linear-gradient(90deg, #7c3aed, #a78bfa);
  transition: width 0.5s ease;
}

.progress--error {
  background: linear-gradient(90deg, #ef4444, #f87171);
}

.progress--done {
  background: linear-gradient(90deg, #22c55e, #4ade80);
}

.space-y-3 > * + * {
  margin-top: 12px;
}

.space-y-2 > * + * {
  margin-top: 8px;
}

.glass-input {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 10px 16px;
  color: #fff;
  font-size: 0.875rem;
  outline: none;
  transition: border-color 0.2s;
}

.glass-input:focus {
  border-color: rgba(124, 58, 237, 0.4);
}

.glass-input::placeholder {
  color: rgba(255, 255, 255, 0.3);
}
</style>
