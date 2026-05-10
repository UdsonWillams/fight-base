const WEIGHT_CLASSES: Record<string, string> = {
  Flyweight: 'Peso-Mosca',
  Bantamweight: 'Peso-Galo',
  Featherweight: 'Peso-Pena',
  Lightweight: 'Peso-Leve',
  Welterweight: 'Peso-Meio-Médio',
  Middleweight: 'Peso-Médio',
  'Light Heavyweight': 'Peso-Meio-Pesado',
  Heavyweight: 'Peso-Pesado',
  "Women's Strawweight": 'Peso-Palha Feminino',
  "Women's Flyweight": 'Peso-Mosca Feminino',
  "Women's Bantamweight": 'Peso-Galo Feminino',
  "Women's Featherweight": 'Peso-Pena Feminino',
  'Catch Weight': 'Peso Casado',
  'Open Weight': 'Peso Aberto',
}

const WEIGHT_CLASSES_REVERSE: Record<string, string> = Object.entries(WEIGHT_CLASSES).reduce(
  (acc, [en, pt]) => {
    acc[pt] = en
    return acc
  },
  {} as Record<string, string>
)

export function translateWeightClass(wc: string | null | undefined): string {
  if (!wc) return 'N/A'
  const normalized = wc.toLowerCase()
  for (const [key, value] of Object.entries(WEIGHT_CLASSES)) {
    if (key.toLowerCase() === normalized) {
      return value
    }
  }
  return wc
}

export function translateWeightClassToEnglish(wc: string | null | undefined): string | null {
  if (!wc) return null
  return WEIGHT_CLASSES_REVERSE[wc] || wc
}

const FIGHTING_STYLES: Record<string, string> = {
  Striker: 'Trocador',
  Grappler: 'Agarrador',
  'All-around': 'Completo',
  'Mixed Martial Arts': 'MMA',
}

export function translateFightingStyle(style: string | null | undefined): string {
  if (!style) return ''
  return FIGHTING_STYLES[style] || style
}

const STANCES: Record<string, string> = {
  Orthodox: 'Destro',
  Southpaw: 'Canhoto',
  Switch: 'Ambidestro',
}

export function translateStance(stance: string | null | undefined): string {
  if (!stance) return ''
  return STANCES[stance] || stance
}

const RESULT_TYPES: Record<string, string> = {
  knockout: 'Nocaute (KO)',
  submission: 'Finalização',
  decision: 'Decisão',
  technical_knockout: 'Nocaute Técnico (TKO)',
  disqualification: 'Desqualificação',
  draw: 'Empate',
}

export function translateResultType(type: string | null | undefined): string {
  if (!type) return ''
  return RESULT_TYPES[type] || type
}

const GENDERS: Record<string, string> = {
  male: 'Masculino',
  female: 'Feminino',
}

export function translateGender(gender: string | null | undefined): string {
  if (!gender) return ''
  return GENDERS[gender] || gender
}
