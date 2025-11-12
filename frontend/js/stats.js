// UFC Dataset Statistics Module

// Load UFC Statistics
async function loadUFCStats() {
    const container = document.getElementById("ufcStatsContent");

    try {
        container.innerHTML =
            '<div class="loading">Carregando estatísticas...</div>';

        // Buscar estatísticas gerais
        const statsResponse = await fetch(`${API_BASE_URL}/fighters/?limit=1`);
        const statsData = await statsResponse.json();

        // Buscar top lutadores por vitórias
        const topWinnersResponse = await fetch(
            `${API_BASE_URL}/fighters/?sort_by=wins&order=desc&limit=10`
        );
        const topWinnersData = await topWinnersResponse.json();

        displayUFCStats(statsData, topWinnersData);
    } catch (error) {
        console.error("Error loading UFC stats:", error);
        container.innerHTML = `
            <div class="error-message">
                ❌ Erro ao carregar estatísticas
            </div>
        `;
    }
}

// Display UFC Statistics
function displayUFCStats(stats, topWinners) {
    const container = document.getElementById("ufcStatsContent");

    const html = `
        <div class="stats-overview">
            <div class="stat-card-large">
                <div class="stat-icon">🥊</div>
                <div class="stat-value">${stats.total || "2,611"}</div>
                <div class="stat-label">Lutadores UFC</div>
                <div class="stat-description">Dataset completo do UFC Stats</div>
            </div>
            
            <div class="stat-card-large">
                <div class="stat-icon">🎪</div>
                <div class="stat-value">745</div>
                <div class="stat-label">Eventos</div>
                <div class="stat-description">De 1994 até 2025</div>
            </div>
            
            <div class="stat-card-large">
                <div class="stat-icon">⚔️</div>
                <div class="stat-value">8,337</div>
                <div class="stat-label">Lutas Reais</div>
                <div class="stat-description">Com estatísticas detalhadas</div>
            </div>
            
            <div class="stat-card-large">
                <div class="stat-icon">📊</div>
                <div class="stat-value">107</div>
                <div class="stat-label">Categorias</div>
                <div class="stat-description">Incluindo torneios TUF</div>
            </div>
        </div>
        
        <div class="stats-section">
            <h3>🏆 Top 10 Lutadores por Vitórias</h3>
            <div class="top-fighters-list">
                ${
                    topWinners.fighters
                        ? topWinners.fighters
                              .map(
                                  (fighter, index) => `
                    <div class="top-fighter-card" onclick="showFighterDetails('${
                        fighter.id
                    }')">
                        <div class="fighter-rank">#${index + 1}</div>
                        <div class="fighter-info">
                            <div class="fighter-name">${fighter.name}</div>
                            <div class="fighter-record">
                                ${fighter.wins}-${fighter.losses}-${
                                      fighter.draws
                                  }
                            </div>
                        </div>
                        <div class="fighter-stats">
                            <span class="stat-badge">✅ ${
                                fighter.wins
                            } vitórias</span>
                            <span class="stat-badge">📍 ${
                                fighter.stance || "N/A"
                            }</span>
                        </div>
                    </div>
                `
                              )
                              .join("")
                        : "<p>Carregando...</p>"
                }
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stats-section">
                <h3>📈 Tipos de Resultado</h3>
                <div class="result-types">
                    <div class="result-bar">
                        <div class="result-label">Decision</div>
                        <div class="result-progress">
                            <div class="result-fill" style="width: 47%"></div>
                        </div>
                        <div class="result-value">3,886 (47%)</div>
                    </div>
                    <div class="result-bar">
                        <div class="result-label">KO/TKO</div>
                        <div class="result-progress">
                            <div class="result-fill decision" style="width: 33%"></div>
                        </div>
                        <div class="result-value">2,719 (33%)</div>
                    </div>
                    <div class="result-bar">
                        <div class="result-label">Submission</div>
                        <div class="result-progress">
                            <div class="result-fill submission" style="width: 20%"></div>
                        </div>
                        <div class="result-value">1,619 (20%)</div>
                    </div>
                </div>
            </div>
            
            <div class="stats-section">
                <h3>🌍 Estatísticas Globais</h3>
                <div class="global-stats">
                    <div class="global-stat">
                        <span class="global-stat-label">Média SLPM</span>
                        <span class="global-stat-value">2.97</span>
                        <span class="global-stat-desc">Strikes por minuto</span>
                    </div>
                    <div class="global-stat">
                        <span class="global-stat-label">Média Str Acc</span>
                        <span class="global-stat-value">40.9%</span>
                        <span class="global-stat-desc">Acurácia de strikes</span>
                    </div>
                    <div class="global-stat">
                        <span class="global-stat-label">Período</span>
                        <span class="global-stat-value">31 anos</span>
                        <span class="global-stat-desc">1994 - 2025</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="stats-actions">
            <button class="btn btn-primary" onclick="showSection('fightersSection')">
                Ver Todos os Lutadores
            </button>
            <button class="btn btn-secondary" onclick="showSection('eventsSection')">
                Ver Eventos
            </button>
        </div>
    `;

    container.innerHTML = html;
}

// Load Fighter Fight History
async function loadFighterHistory(fighterId) {
    try {
        const response = await fetch(`${API_BASE_URL}/fighters/${fighterId}`);
        const fighter = await response.json();

        if (fighter.cartel && fighter.cartel.length > 0) {
            return displayFighterHistory(fighter);
        }

        return '<p class="text-muted">Sem histórico de lutas disponível</p>';
    } catch (error) {
        console.error("Error loading fighter history:", error);
        return '<p class="error-message">Erro ao carregar histórico</p>';
    }
}

// Display Fighter History
function displayFighterHistory(fighter) {
    if (!fighter.cartel || fighter.cartel.length === 0) {
        return '<p class="text-muted">Sem histórico de lutas disponível</p>';
    }

    const sortedFights = [...fighter.cartel].sort(
        (a, b) => new Date(b.date || 0) - new Date(a.date || 0)
    );

    return `
        <div class="fight-history">
            <h4>Histórico de Lutas (${sortedFights.length} lutas)</h4>
            <div class="fight-history-list">
                ${sortedFights
                    .map(
                        (fight, index) => `
                    <div class="fight-history-item ${
                        fight.result === "win"
                            ? "win"
                            : fight.result === "loss"
                            ? "loss"
                            : "draw"
                    }">
                        <div class="fight-number">#${
                            sortedFights.length - index
                        }</div>
                        <div class="fight-details">
                            <div class="fight-opponent">
                                <span class="result-badge ${fight.result}">
                                    ${
                                        fight.result === "win"
                                            ? "✅"
                                            : fight.result === "loss"
                                            ? "❌"
                                            : "🤝"
                                    }
                                </span>
                                vs ${fight.opponent_name}
                            </div>
                            <div class="fight-method">
                                ${fight.method || "N/A"} 
                                ${fight.round ? `(R${fight.round})` : ""}
                                ${fight.time ? `${fight.time}` : ""}
                            </div>
                            ${
                                fight.date
                                    ? `
                                <div class="fight-date">
                                    📅 ${formatDate(fight.date)}
                                </div>
                            `
                                    : ""
                            }
                        </div>
                    </div>
                `
                    )
                    .join("")}
            </div>
        </div>
    `;
}

// Search Fights
async function searchFights(query) {
    try {
        const response = await fetch(
            `${API_BASE_URL}/fighters/?search=${encodeURIComponent(
                query
            )}&limit=20`
        );
        const data = await response.json();

        return data.fighters || [];
    } catch (error) {
        console.error("Error searching fights:", error);
        return [];
    }
}

// Initialize Stats Page
function initStatsPage() {
    // Load UFC statistics when stats section is shown
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (
                mutation.target.id === "ufcStatsSection" &&
                mutation.target.classList.contains("active")
            ) {
                loadUFCStats();
            }
        });
    });

    const statsSection = document.getElementById("ufcStatsSection");
    if (statsSection) {
        observer.observe(statsSection, {
            attributes: true,
            attributeFilter: ["class"],
        });
    }
}

// Helper function to format date
function formatDate(dateString) {
    if (!dateString) return "N/A";

    const date = new Date(dateString);
    const options = { year: "numeric", month: "short", day: "numeric" };
    return date.toLocaleDateString("pt-BR", options);
}
