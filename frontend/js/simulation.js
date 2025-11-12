// Simulation Module

// Run simulation
async function runSimulation() {
    if (!requireAuth()) return;

    // Use selected fighters from search
    const fighter1Id = selectedFighter1;
    const fighter2Id = selectedFighter2;
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
            <button onclick="runSimulation()" class="btn btn-primary">Simular Novamente</button>
        </div>
    `;

    container.style.display = "block";
    container.scrollIntoView({ behavior: "smooth", block: "center" });
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
        const gender = document.getElementById("rankingGender").value;
        const weight_class = document.getElementById("rankingWeight").value;

        const params = { limit: 10 };
        if (organization) params.last_organization_fight = organization;
        if (gender) params.gender = gender;
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
