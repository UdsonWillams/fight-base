export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return ''
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return ''

  return date.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

interface FighterRecord {
  record?: string
  wins?: number
  losses?: number
  draws?: number
}

export function formatRecord(fighter: FighterRecord | null | undefined): string {
  if (!fighter) return '0-0-0'
  if (fighter.record) return fighter.record
  const wins = fighter.wins || 0
  const losses = fighter.losses || 0
  const draws = fighter.draws || 0
  return `${wins}-${losses}-${draws}`
}

export function formatHeight(height: number | null | undefined): string {
  if (height === null || height === undefined) return 'N/A'
  return `${height} cm`
}

export function formatWeight(weight: number | null | undefined): string {
  if (weight === null || weight === undefined) return 'N/A'
  return `${weight} kg`
}

export function getOverallColor(overall: number): string {
  if (overall >= 90) return '#FFD700'
  if (overall >= 85) return '#FF4655'
  if (overall >= 75) return '#FFB700'
  if (overall >= 65) return '#4CAF50'
  return '#666'
}

export function capitalize(str: string | null | undefined): string {
  if (!str) return ''
  return str.charAt(0).toUpperCase() + str.slice(1)
}

export function escapeHTML(str: string | null | undefined): string {
  if (str === null || str === undefined) return ''
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

export function formatPercentage(value: number): string {
  return `${Math.round(value)}%`
}
