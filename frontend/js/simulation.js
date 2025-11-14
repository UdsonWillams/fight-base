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

// Display simulation result with live animation
async function displaySimulationResult(result) {
    const container = document.getElementById("simulationResult");
    container.style.display = "block";
    container.innerHTML = "";

    // Debug: verificar dados
    console.log("Simulation result:", {
        fighter1: result.fighter1_name,
        fighter2: result.fighter2_name,
        winner: result.winner_name,
        result_type: result.result_type,
        finish_round: result.finish_round,
        rounds: result.rounds,
        total_rounds_simulated: result.simulation_details?.rounds?.length,
        fighter1_prob: result.fighter1_probability,
        fighter2_prob: result.fighter2_probability,
    });

    // Se tiver simulation_details, animar round por round
    if (result.simulation_details?.rounds?.length > 0) {
        await animateFightLive(result, container);
    } else {
        // Fallback para exibição estática
        displayStaticResult(result, container);
    }
}

// Animate fight in real-time
async function animateFightLive(result, container) {
    const {
        simulation_details,
        fighter1_name,
        fighter2_name,
        fighter1_id,
        fighter2_id,
    } = result;

    // Buscar fotos dos lutadores
    const fighter1Photo = await getFighterPhotoUrl(fighter1_id);
    const fighter2Photo = await getFighterPhotoUrl(fighter2_id);

    // Container principal da animação
    const animationContainer = document.createElement("div");
    animationContainer.className = "fight-animation";
    animationContainer.innerHTML = `
        <div class="fight-header">
            <div class="fighter-corner fighter-1">
                <div class="fighter-photo" id="fighter1Photo">
                    ${
                        fighter1Photo
                            ? `<img src="${fighter1Photo}" alt="${fighter1_name}" onerror="this.parentElement.innerHTML='🥊'" />`
                            : "🥊"
                    }
                </div>
                <h3>${fighter1_name}</h3>
                <div class="corner-probability" style="font-size: 1.5rem; color: var(--primary); font-weight: bold; margin: 0.5rem 0;">
                    ${result.fighter1_probability}%
                </div>
                <small style="color: var(--text-light); display: block; margin-bottom: 0.5rem;">Probabilidade de vitória</small>
                <div class="corner-score" id="fighter1Score">0</div>
                <div class="corner-strikes" id="fighter1Strikes" style="display: none;">0 golpes</div>
            </div>
            <div class="fight-status">
                <div class="round-indicator" id="roundIndicator">Preparando...</div>
                <div class="time-bar-container">
                    <div class="time-bar" id="timeBar"></div>
                </div>
            </div>
            <div class="fighter-corner fighter-2">
                <div class="fighter-photo" id="fighter2Photo">
                    ${
                        fighter2Photo
                            ? `<img src="${fighter2Photo}" alt="${fighter2_name}" onerror="this.parentElement.innerHTML='🥊'" />`
                            : "🥊"
                    }
                </div>
                <h3>${fighter2_name}</h3>
                <div class="corner-probability" style="font-size: 1.5rem; color: var(--primary); font-weight: bold; margin: 0.5rem 0;">
                    ${result.fighter2_probability}%
                </div>
                <small style="color: var(--text-light); display: block; margin-bottom: 0.5rem;">Probabilidade de vitória</small>
                <div class="corner-score" id="fighter2Score">0</div>
                <div class="corner-strikes" id="fighter2Strikes" style="display: none;">0 golpes</div>
            </div>
        </div>
        <div class="fight-events" id="fightEvents"></div>
        <div class="fight-controls">
            <button id="skipAnimation" class="btn btn-secondary btn-sm">Pular Animação</button>
        </div>
    `;

    container.appendChild(animationContainer);
    container.scrollIntoView({ behavior: "smooth", block: "start" });

    let skipRequested = false;
    document.getElementById("skipAnimation").addEventListener("click", () => {
        skipRequested = true;
    });

    // Rastrear golpes acumulados
    let fighter1TotalStrikes = 0;
    let fighter2TotalStrikes = 0;

    // Animar cada round
    for (let i = 0; i < simulation_details.rounds.length; i++) {
        if (skipRequested) break;

        const round = simulation_details.rounds[i];
        const roundStrikes = await animateRound(
            round,
            i === simulation_details.rounds.length - 1,
            result,
            fighter1TotalStrikes,
            fighter2TotalStrikes
        );

        // Acumular golpes
        fighter1TotalStrikes = roundStrikes.fighter1Total;
        fighter2TotalStrikes = roundStrikes.fighter2Total;

        if (skipRequested) break;

        // Pausa entre rounds (exceto no último)
        if (i < simulation_details.rounds.length - 1) {
            await showRoundBreak();
        }
    }

    // Mostrar resultado final
    await showFinalResult(result, container, skipRequested);
}

// Animate a single round
async function animateRound(
    round,
    isLastRound,
    result,
    fighter1PrevTotal,
    fighter2PrevTotal
) {
    const roundIndicator = document.getElementById("roundIndicator");
    const timeBar = document.getElementById("timeBar");
    const eventsContainer = document.getElementById("fightEvents");

    // Anunciar início do round
    roundIndicator.textContent = `ROUND ${round.round_number}`;
    roundIndicator.className = "round-indicator round-start";
    await delay(1500);

    roundIndicator.className = "round-indicator";

    // Animar barra de tempo - mais devagar para melhor visualização
    const roundDuration = 6000; // 6 segundos por round na animação
    const eventDelay = roundDuration / (round.events.length + 1);

    // Usar os pontos do round como golpes significativos do round atual
    const fighter1RoundStrikes = Math.round(round.fighter1_points);
    const fighter2RoundStrikes = Math.round(round.fighter2_points);

    // Calcular total acumulado
    const fighter1TotalStrikes = fighter1PrevTotal + fighter1RoundStrikes;
    const fighter2TotalStrikes = fighter2PrevTotal + fighter2RoundStrikes;

    timeBar.style.transition = `width ${roundDuration}ms linear`;
    timeBar.style.width = "100%";

    // Mostrar eventos do round
    for (let i = 0; i < round.events.length; i++) {
        await delay(eventDelay);

        const eventDiv = document.createElement("div");
        eventDiv.className = "fight-event animate-fade-in";

        // Emojis para diferentes tipos de eventos
        let emoji = "🥊";
        const eventText = round.events[i].toLowerCase();
        if (
            eventText.includes("finalização") ||
            eventText.includes("submission")
        ) {
            emoji = "🔒";
            eventDiv.classList.add("critical-event");
        } else if (
            eventText.includes("knockdown") ||
            eventText.includes("derrubou")
        ) {
            emoji = "💥";
            eventDiv.classList.add("critical-event");
        } else if (
            eventText.includes("takedown") ||
            eventText.includes("queda")
        ) {
            emoji = "🤼";
        } else if (eventText.includes("dominou")) {
            emoji = "💪";
        }

        eventDiv.innerHTML = `
            <span class="event-icon">${emoji}</span>
            <span class="event-text">${round.events[i]}</span>
        `;

        eventsContainer.appendChild(eventDiv);
        eventsContainer.scrollTop = eventsContainer.scrollHeight;
    }

    // Finalizar barra de tempo
    await delay(eventDelay);
    timeBar.style.width = "0%";
    timeBar.style.transition = "width 0.3s ease";

    // Mostrar placar do round
    document.getElementById("fighter1Score").textContent =
        round.fighter1_points.toFixed(1);
    document.getElementById("fighter2Score").textContent =
        round.fighter2_points.toFixed(1);

    // Mostrar e atualizar golpes significativos ACUMULADOS no final do round
    const fighter1StrikesEl = document.getElementById("fighter1Strikes");
    const fighter2StrikesEl = document.getElementById("fighter2Strikes");

    fighter1StrikesEl.textContent = `${fighter1TotalStrikes} golpes`;
    fighter2StrikesEl.textContent = `${fighter2TotalStrikes} golpes`;
    fighter1StrikesEl.style.display = "block";
    fighter2StrikesEl.style.display = "block";

    // Mostrar resumo do round com golpes DO ROUND (não acumulado)
    const roundSummary = document.createElement("div");
    roundSummary.className = "round-summary animate-fade-in";
    roundSummary.innerHTML = `
        <strong>Fim do Round ${round.round_number}</strong><br>
        Golpes do Round: ${result.fighter1_name} ${fighter1RoundStrikes} - ${fighter2RoundStrikes} ${result.fighter2_name}
    `;
    eventsContainer.appendChild(roundSummary);

    await delay(800);

    // Retornar totais acumulados
    return {
        fighter1Total: fighter1TotalStrikes,
        fighter2Total: fighter2TotalStrikes,
    };
}

// Show break between rounds
async function showRoundBreak() {
    const roundIndicator = document.getElementById("roundIndicator");
    roundIndicator.textContent = "Intervalo entre rounds...";
    roundIndicator.className = "round-indicator round-break";
    await delay(2000);
}

// Helper to get fighter photo URL
async function getFighterPhotoUrl(fighterId) {
    try {
        const response = await api.listFighterPhotos(fighterId);
        if (response && response.length > 0) {
            return response[0]; // Primeira foto
        }
    } catch (error) {
        console.log("No photo found for fighter:", fighterId);
    }
    return null; // Retorna null para usar fallback de luva
}

// Show final result
async function showFinalResult(result, container, wasSkipped) {
    const fightAnimation = container.querySelector(".fight-animation");
    if (fightAnimation && !wasSkipped) {
        await delay(500);
    }

    // Criar card com predição vs resultado
    const resultCard = document.createElement("div");
    resultCard.className = "result-winner animate-fade-in";
    resultCard.innerHTML = `
        <div style="background: linear-gradient(135deg, var(--primary), var(--accent)); padding: 3rem 2rem; border-radius: 8px; text-align: center; color: white; margin-bottom: 2rem;">
            <h2 style="color: white; margin-bottom: 1rem;">🏆 VENCEDOR</h2>
            <h1 style="font-size: 3rem; margin: 1rem 0; color: white;">${
                result.winner_name
            }</h1>
            <p style="font-size: 1.5rem; margin-top: 1rem; color: white;">
                Por ${formatResultType(result.result_type)}
                ${result.finish_round ? ` no Round ${result.finish_round}` : ""}
            </p>
        </div>

        <div style="background: var(--card-bg); padding: 2rem; border-radius: 8px; margin-bottom: 2rem;">
            <h3 style="text-align: center; color: var(--text-light); margin-bottom: 1.5rem;">Probabilidade pré-luta</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                <div style="text-align: center;">
                    <h3>${result.fighter1_name}</h3>
                    <div style="font-size: 2rem; color: var(--primary); margin: 1rem 0;">
                        ${result.fighter1_probability}%
                    </div>
                    <p style="color: var(--text-light);">Probabilidade de vitória</p>
                </div>
                <div style="text-align: center;">
                    <h3>${result.fighter2_name}</h3>
                    <div style="font-size: 2rem; color: var(--primary); margin: 1rem 0;">
                        ${result.fighter2_probability}%
                    </div>
                    <p style="color: var(--text-light);">Probabilidade de vitória</p>
                </div>
            </div>
        </div>

        <div style="text-align: center; margin-top: 2rem;">
            <button id="simulateAgainBtn" class="btn btn-primary">Simular Novamente</button>
        </div>
    `;

    container.appendChild(resultCard);

    // Setup listener for "Simular Novamente" button
    setTimeout(() => {
        const simulateAgainBtn = document.getElementById("simulateAgainBtn");
        if (simulateAgainBtn) {
            simulateAgainBtn.addEventListener("click", runSimulation);
        }
    }, 0);

    resultCard.scrollIntoView({ behavior: "smooth", block: "center" });
}

// Display static result (fallback)
function displayStaticResult(result, container) {
    container.innerHTML = `
        <div class="result-winner animate-fade-in">
            <div style="background: linear-gradient(135deg, var(--primary), var(--accent)); padding: 3rem 2rem; border-radius: 8px; text-align: center; color: white; margin-bottom: 2rem;">
                <h2 style="color: white; margin-bottom: 1rem;">🏆 VENCEDOR</h2>
                <h1 style="font-size: 3rem; margin: 1rem 0; color: white;">${
                    result.winner_name
                }</h1>
                <p style="font-size: 1.5rem; margin-top: 1rem; color: white;">
                    Por ${formatResultType(result.result_type)}
                    ${
                        result.finish_round
                            ? ` no Round ${result.finish_round}`
                            : ""
                    }
                </p>
            </div>

            <div style="background: var(--card-bg); padding: 2rem; border-radius: 8px; margin-bottom: 2rem;">
                <h3 style="text-align: center; color: var(--text-light); margin-bottom: 1.5rem;">Probabilidade pré-luta</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                    <div style="text-align: center;">
                        <h3>${result.fighter1_name}</h3>
                        <div style="font-size: 2rem; color: var(--primary); margin: 1rem 0;">
                            ${result.fighter1_probability}%
                        </div>
                        <p style="color: var(--text-light);">Probabilidade de vitória</p>
                    </div>
                    <div style="text-align: center;">
                        <h3>${result.fighter2_name}</h3>
                        <div style="font-size: 2rem; color: var(--primary); margin: 1rem 0;">
                            ${result.fighter2_probability}%
                        </div>
                        <p style="color: var(--text-light);">Probabilidade de vitória</p>
                    </div>
                </div>
            </div>

            <div style="text-align: center; margin-top: 2rem;">
                <button id="simulateAgainBtn" class="btn btn-primary">Simular Novamente</button>
            </div>
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

// Helper function for delays
function delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
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
