<template>
  <div class="advanced-stats">
    <div class="stats-grid">
      <!-- Striking -->
      <div class="stat-category">
        <h4 class="category-title">
          <span class="category-icon">👊</span>
          Striking (Golpes)
        </h4>
        <div class="stats-row">
          <div class="stat-card glass-card">
            <div class="stat-value" :class="valueColor(slpm, 'slpm')">{{ formatNumber(slpm) }}</div>
            <div class="stat-label">Golpes Significativos / min</div>
            <div class="stat-desc">Golpes que realmente conectam por minuto</div>
          </div>
          <div class="stat-card glass-card">
            <div class="stat-value" :class="valueColor(strAcc, 'percent')">{{ formatPercent(strAcc) }}</div>
            <div class="stat-label">Precisao de Golpes</div>
            <div class="stat-desc">Taxa de acerto dos golpes significativos</div>
          </div>
          <div class="stat-card glass-card">
            <div class="stat-value" :class="valueColor(sapm, 'sapm')">{{ formatNumber(sapm) }}</div>
            <div class="stat-label">Golpes Absorvidos / min</div>
            <div class="stat-desc">Golpes que o lutador leva por minuto (menor = melhor)</div>
          </div>
          <div class="stat-card glass-card">
            <div class="stat-value" :class="valueColor(strDef, 'percent')">{{ formatPercent(strDef) }}</div>
            <div class="stat-label">Defesa de Golpes</div>
            <div class="stat-desc">Porcentagem de golpes do adversario que ele desvia</div>
          </div>
        </div>
      </div>

      <!-- Grappling -->
      <div class="stat-category">
        <h4 class="category-title">
          <span class="category-icon">🤼</span>
          Grappling (Luta no Chao)
        </h4>
        <div class="stats-row">
          <div class="stat-card glass-card">
            <div class="stat-value" :class="valueColor(tdAvg, 'td')">{{ formatNumber(tdAvg) }}</div>
            <div class="stat-label">Quedas / 15 min</div>
            <div class="stat-desc">Media de quedas que ele consegue a cada 15 min</div>
          </div>
          <div class="stat-card glass-card">
            <div class="stat-value" :class="valueColor(tdAcc, 'percent')">{{ formatPercent(tdAcc) }}</div>
            <div class="stat-label">Precisao de Quedas</div>
            <div class="stat-desc">Taxa de sucesso nas tentativas de queda</div>
          </div>
          <div class="stat-card glass-card">
            <div class="stat-value" :class="valueColor(tdDef, 'percent')">{{ formatPercent(tdDef) }}</div>
            <div class="stat-label">Defesa de Quedas</div>
            <div class="stat-desc">Porcentagem de tentativas de queda que ele escapa</div>
          </div>
          <div class="stat-card glass-card">
            <div class="stat-value" :class="valueColor(subAvg, 'sub')">{{ formatNumber(subAvg) }}</div>
            <div class="stat-label">Finalizacoes / 15 min</div>
            <div class="stat-desc">Media de tentativas de finalizacao a cada 15 min</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  slpm: number | null
  strAcc: number | null
  sapm: number | null
  strDef: number | null
  tdAvg: number | null
  tdAcc: number | null
  tdDef: number | null
  subAvg: number | null
}>()

function formatNumber(val: number | null): string {
  if (val == null) return '-'
  return val.toFixed(2)
}

function formatPercent(val: number | null): string {
  if (val == null) return '-'
  return val.toFixed(1) + '%'
}

function valueColor(val: number | null, type: string): string {
  if (val == null) return 'text-white/30'

  // Para stats onde MAIOR é melhor
  const higherIsBetter = ['slpm', 'strAcc', 'tdAvg', 'tdAcc', 'tdDef', 'subAvg', 'percent']
  // Para stats onde MENOR é melhor
  const lowerIsBetter = ['sapm']

  if (type === 'percent') {
    if (val >= 60) return 'text-green-400'
    if (val >= 45) return 'text-yellow-400'
    return 'text-red-400'
  }

  if (type === 'slpm') {
    if (val >= 5) return 'text-green-400'
    if (val >= 3) return 'text-yellow-400'
    return 'text-red-400'
  }

  if (type === 'sapm') {
    // Menor é melhor
    if (val <= 2.5) return 'text-green-400'
    if (val <= 4) return 'text-yellow-400'
    return 'text-red-400'
  }

  if (type === 'td') {
    if (val >= 2) return 'text-green-400'
    if (val >= 1) return 'text-yellow-400'
    return 'text-red-400'
  }

  if (type === 'sub') {
    if (val >= 1.5) return 'text-green-400'
    if (val >= 0.5) return 'text-yellow-400'
    return 'text-red-400'
  }

  return 'text-purple-400'
}
</script>

<style scoped>
.advanced-stats {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.stats-grid {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.stat-category {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.category-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  padding-bottom: 8px;
  border-bottom: 1px solid var(--glass-border);
}

.category-icon {
  font-size: 1.2rem;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  gap: 12px;
}

@media (min-width: 640px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .stats-row {
    grid-template-columns: repeat(4, 1fr);
  }
}

.stat-card {
  padding: 16px;
  text-align: center;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.05);
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 800;
  margin-bottom: 6px;
  line-height: 1;
}

.stat-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.stat-desc {
  font-size: 0.7rem;
  color: var(--text-muted);
  line-height: 1.3;
}
</style>
