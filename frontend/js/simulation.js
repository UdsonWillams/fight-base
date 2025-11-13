// Simulation Module

let fighterSearchInitialized = false;

// Setup simulation-specific event listeners
function setupSimulationListeners() {
    // Setup fighter search
    setupFighterSearch();

    // Setup simulate button
    const simulateBtn = document.getElementById("simulateBtn");
    if (simulateBtn) {
        simulateBtn.addEventListener("click", runSimulation);
    }

    // Setup rounds select
    const roundsSelect = document.getElementById("roundsSelect");
    if (roundsSelect) {
        roundsSelect.addEventListener("change", () => {
            console.log("Rounds changed to:", roundsSelect.value);
        });
    }
}

// Setup fighter search functionality
function setupFighterSearch() {
    if (fighterSearchInitialized) {
        return;
    }

    const input1 = document.getElementById("fighter1Search");
    const input2 = document.getElementById("fighter2Search");

    if (!input1 || !input2) {
        console.error("Fighter search inputs not found");
        return;
    }

    // Fighter 1 search
    input1.addEventListener("input", (e) => {
        debounceSearch(e.target.value, "fighter1Results", 1);
    });

    // Fighter 2 search
    input2.addEventListener("input", (e) => {
        debounceSearch(e.target.value, "fighter2Results", 2);
    });

    // Event delegation for search results (Fighter 1)
    const fighter1Results = document.getElementById("fighter1Results");
    if (fighter1Results) {
        fighter1Results.addEventListener("click", (e) => {
            const resultItem = e.target.closest(".search-result-item");
            if (resultItem) {
                const fighterId = resultItem.dataset.fighterId;
                const fighterNum = parseInt(resultItem.dataset.fighterNum);
                if (fighterId && fighterNum) {
                    selectFighter(fighterId, fighterNum);
                }
            }
        });
    }

    // Event delegation for search results (Fighter 2)
    const fighter2Results = document.getElementById("fighter2Results");
    if (fighter2Results) {
        fighter2Results.addEventListener("click", (e) => {
            const resultItem = e.target.closest(".search-result-item");
            if (resultItem) {
                const fighterId = resultItem.dataset.fighterId;
                const fighterNum = parseInt(resultItem.dataset.fighterNum);
                if (fighterId && fighterNum) {
                    selectFighter(fighterId, fighterNum);
                }
            }
        });
    }

    // Close search results when clicking outside
    document.addEventListener("click", (e) => {
        if (!e.target.closest(".fighter-search-container")) {
            document.getElementById("fighter1Results").classList.remove("show");
            document.getElementById("fighter2Results").classList.remove("show");
        }
    });

    fighterSearchInitialized = true;
}

// Debounce search input
function debounceSearch(query, resultsId, fighterNum) {
    clearTimeout(AppState.searchTimeout);

    const resultsContainer = document.getElementById(resultsId);

    if (query.length < 2) {
        resultsContainer.classList.remove("show");
        return;
    }

    // Show loading
    resultsContainer.innerHTML =
        '<div class="search-loading">Buscando...</div>';
    resultsContainer.classList.add("show");

    AppState.searchTimeout = setTimeout(() => {
        searchFightersForSimulation(query, resultsId, fighterNum);
    }, 300);
}

// Search fighters for simulation
async function searchFightersForSimulation(query, resultsId, fighterNum) {
    try {
        const response = await api.getFighters({
            name: query,
            limit: 10,
        });

        displaySearchResults(response.fighters, resultsId, fighterNum);
    } catch (error) {
        console.error("Error searching fighters:", error);
        const resultsContainer = document.getElementById(resultsId);
        resultsContainer.innerHTML =
            '<div class="search-no-results">Erro ao buscar lutadores</div>';
    }
}

// Display search results
function displaySearchResults(fighters, resultsId, fighterNum) {
    const resultsContainer = document.getElementById(resultsId);

    if (!fighters || fighters.length === 0) {
        resultsContainer.innerHTML =
            '<div class="search-no-results">Nenhum lutador encontrado</div>';
        return;
    }

    resultsContainer.innerHTML = fighters
        .map(
            (fighter) => `
        <div class="search-result-item" data-fighter-id="${
            fighter.id
        }" data-fighter-num="${fighterNum}">
            <div class="search-result-name">${fighter.name}</div>
            <div class="search-result-info">
                ${fighter.nickname ? `<span>"${fighter.nickname}"</span>` : ""}
                <span>${
                    fighter.last_organization_fight ||
                    fighter.organization ||
                    "N/A"
                }</span>
                <span>${
                    typeof translateWeightClass !== "undefined"
                        ? translateWeightClass(
                              fighter.actual_weight_class ||
                                  fighter.weight_class
                          )
                        : fighter.actual_weight_class ||
                          fighter.weight_class ||
                          "N/A"
                }</span>
                ${
                    fighter.record
                        ? `<span>Record: ${fighter.record}</span>`
                        : ""
                }
            </div>
        </div>
    `
        )
        .join("");
}

// Select fighter
function selectFighter(fighterId, fighterNum) {
    console.log("selectFighter called:", { fighterId, fighterNum });

    const searchInput =
        fighterNum === 1
            ? document.getElementById("fighter1Search")
            : document.getElementById("fighter2Search");
    const resultsContainer =
        fighterNum === 1
            ? document.getElementById("fighter1Results")
            : document.getElementById("fighter2Results");

    // Store selected fighter
    AppState.setSelectedFighter(fighterNum, fighterId);
    console.log(
        "Fighter stored in AppState:",
        AppState.getSelectedFighter(fighterNum)
    );

    // Load fighter details and update input
    loadFighterForSelection(fighterId, fighterNum);

    // Hide results
    resultsContainer.classList.remove("show");
}

// Load fighter for selection
async function loadFighterForSelection(fighterId, fighterNum) {
    try {
        const fighter = await api.getFighterById(fighterId);

        const searchInput =
            fighterNum === 1
                ? document.getElementById("fighter1Search")
                : document.getElementById("fighter2Search");

        if (searchInput) {
            searchInput.value = `${fighter.name}${
                fighter.nickname ? ` "${fighter.nickname}"` : ""
            }`;
        }
    } catch (error) {
        console.error("Error loading fighter:", error);
        showToast("Erro ao carregar lutador", "error");
    }
}

// Run simulation
async function runSimulation() {
    if (!requireAuth()) return;

    // Use selected fighters from AppState
    const fighter1Id = AppState.getSelectedFighter(1);
    const fighter2Id = AppState.getSelectedFighter(2);
    const rounds = parseInt(document.getElementById("roundsSelect").value);

    if (!fighter1Id || !fighter2Id) {
        showToast("Selecione ambos os lutadores", "error");
        return;
    }

    if (fighter1Id === fighter2Id) {
        showToast("Selecione lutadores diferentes", "error");
        return;
    }

    try {
        showLoading("Simulando luta...");

        const result = await api.createSimulation({
            fighter1_id: fighter1Id,
            fighter2_id: fighter2Id,
            rounds: rounds,
            notes: null,
        });

        displaySimulationResult(result);
        loadRecentSimulations();
    } catch (error) {
        showToast(error.message || "Erro ao simular luta", "error");
    } finally {
        hideLoading();
    }
}

// Display simulation result
function displaySimulationResult(result) {
    const container = document.getElementById("simulationResult");

    container.innerHTML = `
        <div class="result-winner">
            <h2>🏆 Vencedor</h2>
            <h1>${result.winner_name}</h1>
            <p style="font-size: 1.5rem; margin-top: 1rem;">
                Por ${formatResultType(result.result_type)}
                ${result.finish_round ? ` no Round ${result.finish_round}` : ""}
            </p>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin: 2rem 0;">
            <div style="text-align: center;">
                <h3>${result.fighter1_name}</h3>
                <div style="font-size: 2rem; color: var(--primary); margin: 1rem 0;">
                    ${result.fighter1_probability}%
                </div>
                <p>Probabilidade de vitória</p>
            </div>
            <div style="text-align: center;">
                <h3>${result.fighter2_name}</h3>
                <div style="font-size: 2rem; color: var(--primary); margin: 1rem 0;">
                    ${result.fighter2_probability}%
                </div>
                <p>Probabilidade de vitória</p>
            </div>
        </div>

        ${
            result.round_details && result.round_details.length > 0
                ? `
            <div class="round-details">
                <h3>Detalhes dos Rounds</h3>
                ${result.round_details
                    .map(
                        (round, index) => `
                    <div class="round-item">
                        <strong>Round ${index + 1}</strong>
                        <p>${
                            round.description || `Round ${index + 1} completado`
                        }</p>
                        ${round.damage ? `<p>Dano: ${round.damage}</p>` : ""}
                    </div>
                `
                    )
                    .join("")}
            </div>
        `
                : ""
        }

        <div style="text-align: center; margin-top: 2rem;">
            <button id="simulateAgainBtn" class="btn btn-primary">Simular Novamente</button>
        </div>
    `;

    container.style.display = "block";
    container.scrollIntoView({ behavior: "smooth", block: "center" });

    // Setup listener for "Simular Novamente" button
    setTimeout(() => {
        const simulateAgainBtn = document.getElementById("simulateAgainBtn");
        if (simulateAgainBtn) {
            simulateAgainBtn.addEventListener("click", runSimulation);
        }
    }, 0);
}

// Format result type
function formatResultType(type) {
    const map = {
        KO: "Nocaute (KO)",
        TKO: "Nocaute Técnico (TKO)",
        Submission: "Finalização",
        Decision: "Decisão",
        "Decision (Unanimous)": "Decisão Unânime",
        "Decision (Split)": "Decisão Dividida",
        "Decision (Majority)": "Decisão Majoritária",
    };
    return map[type] || type;
}

// Load recent simulations
async function loadRecentSimulations() {
    try {
        const simulations = await api.getRecentSimulations(5);

        const container = document.getElementById("recentSimsList");

        if (!simulations || simulations.length === 0) {
            container.innerHTML =
                '<p style="text-align:center; color:#666;">Nenhuma simulação recente</p>';
            return;
        }

        container.innerHTML = simulations
            .map(
                (sim) => `
            <div class="round-item" style="margin: 1rem 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>${sim.fighter1_name}</strong> vs <strong>${
                    sim.fighter2_name
                }</strong>
                    </div>
                    <div style="color: var(--primary); font-weight: bold;">
                        ${sim.winner_name} 🏆
                    </div>
                </div>
                <div style="font-size: 0.9rem; color: #666; margin-top: 0.5rem;">
                    ${formatResultType(sim.result_type)}
                    ${sim.rounds ? ` • ${sim.rounds} rounds` : ""}
                </div>
            </div>
        `
            )
            .join("");
    } catch (error) {
        console.error("Error loading recent simulations:", error);
    }
}

// Load rankings
async function loadRankings() {
    try {
        const organization = document.getElementById("rankingOrg").value;
        const weight_class = document.getElementById("rankingWeight").value;

        const params = { limit: 15 };
        if (organization) params.last_organization_fight = organization;
        if (weight_class) params.actual_weight_class = weight_class;

        const fighters = await api.getTopFighters(params);

        const container = document.getElementById("rankingsList");

        if (!fighters || fighters.length === 0) {
            container.innerHTML =
                '<div class="loading">Nenhum lutador encontrado</div>';
            return;
        }

        container.innerHTML = fighters
            .map(
                (fighter, index) => `
            <div class="ranking-item">
                <div class="ranking-position">#${index + 1}</div>
                <div class="ranking-fighter">
                    <div style="font-size: 1.3rem; font-weight: 600;">${
                        fighter.name
                    }</div>
                    ${
                        fighter.nickname
                            ? `<div style="color: #666; font-style: italic;">"${fighter.nickname}"</div>`
                            : ""
                    }
                    <div style="margin-top: 0.5rem;">
                        <span class="meta-badge">${
                            fighter.last_organization_fight ||
                            fighter.organization ||
                            "N/A"
                        }</span>
                        <span class="meta-badge">${formatWeightClass(
                            fighter.actual_weight_class || fighter.weight_class
                        )}</span>
                    </div>
                </div>
                <div class="ranking-overall">${fighter.overall || 75}</div>
            </div>
        `
            )
            .join("");
    } catch (error) {
        console.error("Error loading rankings:", error);
        showToast("Erro ao carregar rankings", "error");
    }
}

// Predict fight (without saving)
async function predictFight(fighter1Id, fighter2Id) {
    try {
        const prediction = await api.predictFight(fighter1Id, fighter2Id);
        return prediction;
    } catch (error) {
        console.error("Error predicting fight:", error);
        return null;
    }
}

// Compare fighters
async function compareFighters(fighter1Id, fighter2Id) {
    try {
        const comparison = await api.compareFighters(fighter1Id, fighter2Id);
        return comparison;
    } catch (error) {
        console.error("Error comparing fighters:", error);
        return null;
    }
}
