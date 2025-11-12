// Utility Functions

// Weight Class Mapping (PT-BR <-> EN)
const WEIGHT_CLASSES = {
    // Men's Divisions
    Flyweight: "Peso-Mosca",
    Bantamweight: "Peso-Galo",
    Featherweight: "Peso-Pena",
    Lightweight: "Peso-Leve",
    Welterweight: "Peso-Meio-Médio",
    Middleweight: "Peso-Médio",
    "Light Heavyweight": "Peso-Meio-Pesado",
    Heavyweight: "Peso-Pesado",

    // Women's Divisions
    "Women's Strawweight": "Peso-Palha Feminino",
    "Women's Flyweight": "Peso-Mosca Feminino",
    "Women's Bantamweight": "Peso-Galo Feminino",
    "Women's Featherweight": "Peso-Pena Feminino",

    // Special Categories
    "Catch Weight": "Peso Casado",
    "Open Weight": "Peso Aberto",
};

// Reverse mapping (PT-BR -> EN)
const WEIGHT_CLASSES_REVERSE = Object.entries(WEIGHT_CLASSES).reduce(
    (acc, [en, pt]) => {
        acc[pt] = en;
        return acc;
    },
    {}
);

/**
 * Converte categoria de peso de inglês para português
 * @param {string} weightClass - Categoria em inglês (ex: "Lightweight")
 * @returns {string} Categoria em português (ex: "Peso-Leve")
 */
function translateWeightClass(weightClass) {
    if (!weightClass) return "N/A";
    return WEIGHT_CLASSES[weightClass] || weightClass;
}

/**
 * Converte categoria de peso de português para inglês
 * @param {string} weightClass - Categoria em português (ex: "Peso-Leve")
 * @returns {string} Categoria em inglês (ex: "Lightweight")
 */
function translateWeightClassToEnglish(weightClass) {
    if (!weightClass) return null;
    return WEIGHT_CLASSES_REVERSE[weightClass] || weightClass;
}

/**
 * Formata o record do lutador (vitórias-derrotas-empates)
 * @param {object} fighter - Objeto do lutador
 * @returns {string} Record formatado (ex: "20-5-0")
 */
function formatRecord(fighter) {
    if (fighter.record) return fighter.record;

    const wins = fighter.wins || 0;
    const losses = fighter.losses || 0;
    const draws = fighter.draws || 0;

    return `${wins}-${losses}-${draws}`;
}

/**
 * Formata altura em centímetros para exibição
 * @param {number} height - Altura em cm
 * @returns {string} Altura formatada (ex: "180 cm")
 */
function formatHeight(height) {
    if (!height) return "N/A";
    return `${height} cm`;
}

/**
 * Formata peso em quilos para exibição
 * @param {number} weight - Peso em kg
 * @returns {string} Peso formatado (ex: "77.5 kg")
 */
function formatWeight(weight) {
    if (!weight) return "N/A";
    return `${weight} kg`;
}

/**
 * Traduz estilo de luta
 * @param {string} style - Estilo em inglês
 * @returns {string} Estilo em português
 */
function translateFightingStyle(style) {
    const styles = {
        Striker: "Trocador",
        Grappler: "Agarrador",
        "All-around": "Completo",
        "Mixed Martial Arts": "MMA",
    };

    return styles[style] || style;
}

/**
 * Traduz stance (postura)
 * @param {string} stance - Postura em inglês
 * @returns {string} Postura em português
 */
function translateStance(stance) {
    const stances = {
        Orthodox: "Ortodoxo",
        Southpaw: "Canhoto",
        Switch: "Alternado",
    };

    return stances[stance] || stance;
}

/**
 * Traduz tipo de resultado da luta
 * @param {string} resultType - Tipo em inglês
 * @returns {string} Tipo em português
 */
function translateResultType(resultType) {
    const types = {
        knockout: "Nocaute (KO)",
        submission: "Finalização",
        decision: "Decisão",
        technical_knockout: "Nocaute Técnico (TKO)",
        disqualification: "Desqualificação",
        draw: "Empate",
    };

    return types[resultType] || resultType;
}

/**
 * Traduz gênero
 * @param {string} gender - Gênero em inglês
 * @returns {string} Gênero em português
 */
function translateGender(gender) {
    const genders = {
        male: "Masculino",
        female: "Feminino",
    };

    return genders[gender] || gender;
}

/**
 * Obtém cor baseada no overall do lutador
 * @param {number} overall - Overall (0-100)
 * @returns {string} Classe CSS ou cor
 */
function getOverallColor(overall) {
    if (overall >= 90) return "#FFD700"; // Ouro
    if (overall >= 85) return "#FF4655"; // Vermelho (primary)
    if (overall >= 75) return "#FFB700"; // Amarelo (accent)
    if (overall >= 65) return "#4CAF50"; // Verde
    return "#666"; // Cinza
}
