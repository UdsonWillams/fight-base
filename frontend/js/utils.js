// Utility Functions

// ============================================
// GERENCIADOR DE ESTADO CENTRALIZADO
// ============================================
const AppState = {
    // Authentication
    currentUser: null,

    // Fighter Selection for Simulation
    selectedFighter1: null,
    selectedFighter2: null,

    // Events
    currentEvent: null,
    eventFights: [],
    editingEventId: null,

    // Fighters
    allFighters: [],
    currentFilters: {},

    // UI State
    loadingOverlay: null,
    searchTimeout: null,

    // Métodos para manipular o estado
    setCurrentUser(user) {
        this.currentUser = user;
    },

    getCurrentUser() {
        return this.currentUser;
    },

    clearUser() {
        this.currentUser = null;
    },

    setSelectedFighter(fighterNum, fighterId) {
        if (fighterNum === 1) {
            this.selectedFighter1 = fighterId;
        } else if (fighterNum === 2) {
            this.selectedFighter2 = fighterId;
        }
    },

    getSelectedFighter(fighterNum) {
        return fighterNum === 1 ? this.selectedFighter1 : this.selectedFighter2;
    },

    clearSelectedFighters() {
        this.selectedFighter1 = null;
        this.selectedFighter2 = null;
    },
};

// ============================================
// FUNÇÕES UTILITÁRIAS GLOBAIS
// ============================================

/**
 * Formata data para exibição
 * @param {string} dateString - Data em formato ISO
 * @returns {string} Data formatada em PT-BR
 */
function formatDate(dateString) {
    if (!dateString) return "";

    const date = new Date(dateString);
    return date.toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}

/**
 * Capitaliza primeira letra de uma string
 * @param {string} str - String para capitalizar
 * @returns {string} String capitalizada
 */
function capitalize(str) {
    if (!str) return "";
    return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Fecha um modal pelo ID
 * @param {string} modalId - ID do modal a ser fechado
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = "none";
        modal.classList.remove("active");
    }
}

/**
 * Mostra um diálogo de confirmação
 * @param {string} title - Título da confirmação
 * @param {string} message - Mensagem da confirmação
 * @returns {Promise<boolean>} Promise que resolve com true/false
 */
async function showConfirm(title, message) {
    return confirm(`${title}\n\n${message}`);
}

/**
 * Mostra notificação toast
 * @param {string} message - Mensagem a exibir
 * @param {string} type - Tipo: 'success', 'error', 'warning', 'info'
 */
function showToast(message, type = "success") {
    const toast = document.getElementById("toast");
    if (!toast) return;

    toast.textContent = message;
    toast.className = `toast ${type} show`;

    setTimeout(() => {
        toast.classList.remove("show");
    }, 3000);
}

/**
 * Mostra overlay de loading
 * @param {string} message - Mensagem de loading
 */
function showLoading(message = "Carregando...") {
    if (!AppState.loadingOverlay) {
        AppState.loadingOverlay = document.createElement("div");
        AppState.loadingOverlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            color: white;
            font-size: 1.5rem;
        `;
        document.body.appendChild(AppState.loadingOverlay);
    }

    AppState.loadingOverlay.innerHTML = `
        <div style="text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">⏳</div>
            <div>${message}</div>
        </div>
    `;
    AppState.loadingOverlay.style.display = "flex";
}

/**
 * Esconde overlay de loading
 */
function hideLoading() {
    if (AppState.loadingOverlay) {
        AppState.loadingOverlay.style.display = "none";
    }
}

// ============================================
// TRADUÇÕES E FORMATAÇÕES
// ============================================

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
