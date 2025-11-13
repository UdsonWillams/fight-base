// Rankings Module

let rankingsData = [];

// Load rankings
async function loadRankings() {
    try {
        showLoading("Carregando rankings...");

        const response = await api.getFighters({ limit: 100, offset: 0 });
        rankingsData = response.fighters || [];

        // Sort by overall rating
        rankingsData.sort((a, b) => {
            const aOverall = getOverallRating(a);
            const bOverall = getOverallRating(b);
            return bOverall - aOverall;
        });

        displayRankings(rankingsData);
    } catch (error) {
        console.error("Error loading rankings:", error);
        showToast("Erro ao carregar rankings", "error");
    } finally {
        hideLoading();
    }
}

// Get overall rating (same logic as fighters.js)
function getOverallRating(fighter) {
    if (fighter.overall_rating || fighter.overall) {
        return fighter.overall_rating || fighter.overall;
    }

    if (fighter.striking || fighter.grappling || fighter.defense) {
        const attrs = [
            fighter.striking || 0,
            fighter.grappling || 0,
            fighter.defense || 0,
            fighter.stamina || 0,
            fighter.speed || 0,
            fighter.strategy || 0,
        ].filter((v) => v > 0);

        if (attrs.length > 0) {
            attrs.sort((a, b) => b - a);
            const top4 = attrs.slice(0, 4);
            return top4.reduce((a, b) => a + b, 0) / top4.length;
        }
    }

    const wins = fighter.wins || 0;
    const losses = fighter.losses || 0;
    const total = wins + losses;

    if (total > 0) {
        const winRate = wins / total;
        return 60 + winRate * 35;
    }

    return 75;
}

// Display rankings
function displayRankings(fighters) {
    const container = document.getElementById("rankingsList");

    if (!fighters || fighters.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>📊 Nenhum ranking disponível</p>
            </div>
        `;
        return;
    }

    container.innerHTML = fighters
        .map(
            (fighter, index) => `
        <div class="ranking-item" data-fighter-id="${fighter.id}">
            <div class="ranking-position">#${index + 1}</div>
            <div class="ranking-fighter-info">
                <div class="ranking-fighter-name">${fighter.name}</div>
                <div class="ranking-fighter-meta">
                    ${
                        fighter.last_organization_fight ||
                        fighter.organization ||
                        "UFC"
                    } •
                    ${
                        typeof translateWeightClass !== "undefined"
                            ? translateWeightClass(
                                  fighter.actual_weight_class ||
                                      fighter.weight_class
                              )
                            : fighter.actual_weight_class ||
                              fighter.weight_class ||
                              "N/A"
                    }
                </div>
            </div>
            <div class="ranking-stats">
                <div class="ranking-overall">${Math.round(
                    getOverallRating(fighter)
                )}</div>
                <div class="ranking-record">${fighter.wins || 0}-${
                fighter.losses || 0
            }</div>
            </div>
        </div>
    `
        )
        .join("");
}

// Filter rankings by weight class
function filterRankings() {
    const weightClass = document.getElementById("rankingsWeightFilter").value;

    let filtered = rankingsData;

    if (weightClass) {
        filtered = rankingsData.filter((f) =>
            (f.actual_weight_class || f.weight_class || "")
                .toLowerCase()
                .includes(weightClass.toLowerCase())
        );
    }

    displayRankings(filtered);
}

// Setup rankings event listeners
function setupRankingsListeners() {
    // Weight class filter
    const weightFilter = document.getElementById("rankingsWeightFilter");
    if (weightFilter) {
        weightFilter.addEventListener("change", filterRankings);
    }

    // Click on ranking item to show details
    const rankingsList = document.getElementById("rankingsList");
    if (rankingsList) {
        rankingsList.addEventListener("click", (e) => {
            const rankingItem = e.target.closest(".ranking-item");
            if (rankingItem) {
                const fighterId = rankingItem.dataset.fighterId;
                if (fighterId && typeof showFighterDetails === "function") {
                    showFighterDetails(fighterId);
                }
            }
        });
    }
}
