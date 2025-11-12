// Events Module - Gerenciamento de eventos de MMA

// Inicializa a seção de eventos
async function initEventsSection() {
    try {
        await loadEvents();
        setupEventForm();
    } catch (error) {
        console.error("Erro ao inicializar seção de eventos:", error);
        hideLoading();
    }
}

// Carrega lista de eventos
async function loadEvents(filters = {}) {
    try {
        showLoading("Carregando eventos...");
        const events = await api.getEvents(filters);

        const eventsList = document.getElementById("eventsList");
        if (!events || events.length === 0) {
            eventsList.innerHTML = `
                <div class="empty-state">
                    <p>📅 Nenhum evento encontrado</p>
                    <p class="text-muted">Crie seu primeiro evento de MMA!</p>
                </div>
            `;
            return;
        }

        eventsList.innerHTML = events
            .map(
                (event) => `
            <div class="event-card" onclick="viewEvent('${event.id}')">
                <div class="event-header">
                    <h3>${event.name}</h3>
                    <span class="badge badge-${getStatusColor(
                        event.status
                    )}">${translateStatus(event.status)}</span>
                </div>
                <div class="event-info">
                    <p><strong>📍</strong> ${
                        event.location || "Local não definido"
                    }</p>
                    <p><strong>🏢</strong> ${event.organization}</p>
                    <p><strong>📅</strong> ${formatDate(event.date)}</p>
                    <p><strong>🥊</strong> ${event.fights_count} lutas</p>
                </div>
                ${
                    event.status === "scheduled"
                        ? `<button class="btn btn-primary btn-lg" onclick="event.stopPropagation(); simulateEventClick('${event.id}')">
                        🎲 Simular Todas as Lutas
                    </button>`
                        : `<button class="btn btn-success btn-lg" disabled style="opacity: 0.6; cursor: not-allowed;">
                        ✅ Evento Concluído
                    </button>`
                }
            </div>
        `
            )
            .join("");
    } catch (error) {
        showToast("Erro ao carregar eventos", "error");
        console.error(error);
    } finally {
        hideLoading();
    }
}

// Visualiza detalhes de um evento
async function viewEvent(eventId) {
    try {
        showLoading("Carregando evento...");
        AppState.currentEvent = await api.getEvent(eventId);

        // Mostra modal com detalhes do evento
        showEventDetailsModal(AppState.currentEvent);
    } catch (error) {
        showToast("Erro ao carregar evento", "error");
        console.error(error);
    } finally {
        hideLoading();
    }
}

// Mostra modal com detalhes do evento
function showEventDetailsModal(event) {
    const modal = document.getElementById("eventDetailsModal");
    const content = document.getElementById("eventDetailsContent");

    content.innerHTML = `
        <div class="event-details">
            <div class="event-details-header">
                <h2>${event.name}</h2>
                <span class="badge badge-${getStatusColor(
                    event.status
                )}">${translateStatus(event.status)}</span>
            </div>

            <div class="event-details-info">
                <p><strong>Organização:</strong> ${event.organization}</p>
                <p><strong>Data:</strong> ${formatDate(event.date)}</p>
                <p><strong>Local:</strong> ${
                    event.location || "Não definido"
                }</p>
                ${
                    event.description
                        ? `<p><strong>Descrição:</strong> ${event.description}</p>`
                        : ""
                }
            </div>

            <h3>Card de Lutas</h3>
            <div class="fights-list">
                ${
                    event.fights && event.fights.length > 0
                        ? event.fights
                              .map((fight) => renderFightCard(fight))
                              .join("")
                        : '<p class="text-muted">Nenhuma luta adicionada</p>'
                }
            </div>

            ${
                event.status === "scheduled"
                    ? `
                <div class="event-actions">
                    <button class="btn btn-primary btn-lg" onclick="simulateCurrentEvent()">
                        🎲 Simular Todas as Lutas
                    </button>
                </div>
            `
                    : ""
            }
        </div>
    `;

    modal.style.display = "flex";
}

// Renderiza card de luta
function renderFightCard(fight) {
    const getFightTypeLabel = (type) => {
        const types = {
            main: "🏆 Main Event",
            "co-main": "⭐ Co-Main Event",
            prelim: "🎬 Prelim",
            standard: "🥊 Fight Card",
        };
        return types[type] || type;
    };

    const isSimulated = fight.status === "simulated";

    return `
        <div class="fight-card ${isSimulated ? "simulated" : ""}">
            <div class="fight-order">
                ${getFightTypeLabel(fight.fight_type)}
                ${
                    fight.is_title_fight
                        ? ' <span class="badge badge-warning">Luta de Título</span>'
                        : ""
                }
            </div>

            <div class="fight-matchup">
                <div class="fighter-info">
                    <strong>${fight.fighter1?.name || "Fighter 1"}</strong>
                    ${
                        fight.fighter1?.nickname
                            ? `<span class="nickname">"${fight.fighter1.nickname}"</span>`
                            : ""
                    }
                    ${
                        isSimulated && fight.winner_id === fight.fighter1_id
                            ? ' <span class="winner-badge">🏆 VENCEDOR</span>'
                            : ""
                    }
                </div>

                <div class="vs">VS</div>

                <div class="fighter-info">
                    <strong>${fight.fighter2?.name || "Fighter 2"}</strong>
                    ${
                        fight.fighter2?.nickname
                            ? `<span class="nickname">"${fight.fighter2.nickname}"</span>`
                            : ""
                    }
                    ${
                        isSimulated && fight.winner_id === fight.fighter2_id
                            ? ' <span class="winner-badge">🏆 VENCEDOR</span>'
                            : ""
                    }
                </div>
            </div>

            ${
                isSimulated
                    ? `
                <div class="fight-result">
                    <p><strong>Resultado:</strong> ${fight.result_type}${
                          fight.finish_round
                              ? ` - Round ${fight.finish_round}`
                              : ""
                      }${fight.finish_time ? ` (${fight.finish_time})` : ""}</p>
                    ${
                        fight.method_details
                            ? `<p><strong>Método:</strong> ${fight.method_details}</p>`
                            : ""
                    }
                    <p><strong>Probabilidades:</strong> ${
                        fight.fighter1?.name
                    } ${fight.fighter1_probability}% vs ${
                          fight.fighter2?.name
                      } ${fight.fighter2_probability}%</p>
                </div>
            `
                    : ""
            }

            <div class="fight-meta">
                <span>${fight.rounds} rounds</span>
                ${
                    fight.weight_class
                        ? `<span>${fight.weight_class}</span>`
                        : ""
                }
            </div>
        </div>
    `;
}

// Simula evento (atalho do card)
async function simulateEventClick(eventId) {
    const confirm = await showConfirm(
        "Simular Evento",
        "Deseja simular todas as lutas deste evento? Esta ação não pode ser desfeita."
    );

    if (!confirm) return;

    try {
        showLoading("Simulando evento...");
        const result = await api.simulateEvent(eventId);

        showToast(
            `Evento simulado! ${result.summary.total_fights} lutas realizadas`,
            "success"
        );

        // Mostra resultados
        showSimulationResults(result);

        // Recarrega lista de eventos
        await loadEvents();
    } catch (error) {
        showToast(error.message || "Erro ao simular evento", "error");
        console.error(error);
    } finally {
        hideLoading();
    }
}

// Simula evento atual (do modal)
async function simulateCurrentEvent() {
    if (!AppState.currentEvent) return;
    await simulateEventClick(AppState.currentEvent.id);
    closeModal("eventDetailsModal");
}

// Mostra resultados da simulação
function showSimulationResults(result) {
    const modal = document.getElementById("simulationResultsModal");
    const content = document.getElementById("simulationResultsContent");

    content.innerHTML = `
        <div class="simulation-results">
            <h2>🎉 ${result.event_name} - Resultados</h2>

            <div class="simulation-summary">
                <div class="stat-box">
                    <h3>${result.summary.total_fights}</h3>
                    <p>Total de Lutas</p>
                </div>
                <div class="stat-box">
                    <h3>${result.summary.knockouts}</h3>
                    <p>Nocautes</p>
                </div>
                <div class="stat-box">
                    <h3>${result.summary.submissions}</h3>
                    <p>Finalizações</p>
                </div>
                <div class="stat-box">
                    <h3>${result.summary.decisions}</h3>
                    <p>Decisões</p>
                </div>
                <div class="stat-box">
                    <h3>${result.summary.finish_rate}%</h3>
                    <p>Taxa de Finalização</p>
                </div>
            </div>

            <h3>Resultados das Lutas</h3>
            <div class="fights-results">
                ${result.simulated_fights
                    .map((fight) => renderFightCard(fight))
                    .join("")}
            </div>
        </div>
    `;

    modal.style.display = "flex";
}

// Setup do formulário de criar evento
function setupEventForm() {
    const form = document.getElementById("createEventForm");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        await handleCreateEvent();
    });

    // Botão para adicionar luta
    const addFightBtn = document.getElementById("addFightBtn");
    if (addFightBtn) {
        addFightBtn.addEventListener("click", addFightToForm);
    }
}

// Adiciona luta ao formulário
function addFightToForm() {
    const fightsContainer = document.getElementById("eventFightsContainer");
    const fightIndex = AppState.eventFights.length + 1;

    const fightHtml = `
        <div class="fight-form-item" data-fight-index="${fightIndex}">
            <h4>Luta ${fightIndex}</h4>

            <div class="form-row">
                <div class="form-group">
                    <label>Lutador 1</label>
                    <input type="text" class="fighter-search" data-fight="${fightIndex}" data-fighter="1" placeholder="Buscar lutador...">
                    <div class="search-results" id="searchResults_${fightIndex}_1"></div>
                    <input type="hidden" id="fighter1_${fightIndex}">
                </div>

                <div class="form-group">
                    <label>Lutador 2</label>
                    <input type="text" class="fighter-search" data-fight="${fightIndex}" data-fighter="2" placeholder="Buscar lutador...">
                    <div class="search-results" id="searchResults_${fightIndex}_2"></div>
                    <input type="hidden" id="fighter2_${fightIndex}">
                </div>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label>Tipo de Luta</label>
                    <select id="fightType_${fightIndex}">
                        <option value="standard">Fight Card</option>
                        <option value="prelim">Prelim</option>
                        <option value="co-main">Co-Main Event</option>
                        <option value="main">Main Event</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>Rounds</label>
                    <select id="rounds_${fightIndex}">
                        <option value="3">3 Rounds</option>
                        <option value="5">5 Rounds</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>
                        <input type="checkbox" id="isTitle_${fightIndex}">
                        Luta de Título
                    </label>
                </div>
            </div>

            <button type="button" class="btn btn-danger btn-sm" onclick="removeFight(${fightIndex})">
                Remover Luta
            </button>
        </div>
    `;

    fightsContainer.insertAdjacentHTML("beforeend", fightHtml);
    AppState.eventFights.push({ index: fightIndex });

    // Setup busca de lutadores
    setupFighterSearchForFight(fightIndex);
}

// Setup busca de lutadores para uma luta
function setupFighterSearchForFight(fightIndex) {
    const inputs = document.querySelectorAll(
        `input.fighter-search[data-fight="${fightIndex}"]`
    );

    inputs.forEach((input) => {
        let searchTimeout;

        input.addEventListener("input", async (e) => {
            clearTimeout(searchTimeout);
            const query = e.target.value;
            const fighterNum = input.dataset.fighter;

            if (query.length < 2) {
                const resultsDiv = document.getElementById(
                    `searchResults_${fightIndex}_${fighterNum}`
                );
                resultsDiv.innerHTML = "";
                resultsDiv.style.display = "none";
                return;
            }

            searchTimeout = setTimeout(async () => {
                try {
                    const response = await api.getFighters({
                        name: query,
                        limit: 5,
                    });

                    console.log("Response from API:", response);

                    // Trata diferentes formatos de resposta
                    let fighters = [];
                    if (Array.isArray(response)) {
                        fighters = response;
                    } else if (response && response.fighters) {
                        fighters = response.fighters;
                    } else if (response && response.data) {
                        fighters = response.data;
                    }

                    console.log("Fighters found:", fighters);

                    displayFighterSearchResults(
                        fighters,
                        fightIndex,
                        fighterNum
                    );
                } catch (error) {
                    console.error("Erro ao buscar lutadores:", error);
                    const resultsDiv = document.getElementById(
                        `searchResults_${fightIndex}_${fighterNum}`
                    );
                    resultsDiv.innerHTML =
                        '<p class="error-message">Erro ao buscar lutadores</p>';
                }
            }, 300);
        });
    });
}

// Exibe resultados da busca de lutadores
function displayFighterSearchResults(fighters, fightIndex, fighterNum) {
    const resultsDiv = document.getElementById(
        `searchResults_${fightIndex}_${fighterNum}`
    );

    if (!fighters || fighters.length === 0) {
        resultsDiv.innerHTML =
            '<p class="no-results">Nenhum lutador encontrado</p>';
        resultsDiv.style.display = "block";
        return;
    }

    resultsDiv.innerHTML = fighters
        .map(
            (fighter) => `
        <div class="search-result-item" onclick="selectFighterForEvent(${fightIndex}, ${fighterNum}, '${
                fighter.id
            }', '${fighter.name.replace(/'/g, "\\'")}')">
            <strong>${fighter.name}</strong>
            ${
                fighter.nickname
                    ? `<span class="nickname">"${fighter.nickname}"</span>`
                    : ""
            }
            <small>${fighter.actual_weight_class || ""} ${
                fighter.gender
                    ? "(" + (fighter.gender === "male" ? "M" : "F") + ")"
                    : ""
            }</small>
        </div>
    `
        )
        .join("");

    resultsDiv.style.display = "block";
}

// Seleciona lutador para o evento
function selectFighterForEvent(fightIndex, fighterNum, fighterId, fighterName) {
    const input = document.querySelector(
        `input.fighter-search[data-fight="${fightIndex}"][data-fighter="${fighterNum}"]`
    );
    const hiddenInput = document.getElementById(
        `fighter${fighterNum}_${fightIndex}`
    );

    input.value = fighterName;
    hiddenInput.value = fighterId;

    // Limpa e esconde resultados
    const resultsDiv = document.getElementById(
        `searchResults_${fightIndex}_${fighterNum}`
    );
    resultsDiv.innerHTML = "";
    resultsDiv.style.display = "none";
}

// Remove luta do formulário
function removeFight(fightIndex) {
    const fightElement = document.querySelector(
        `.fight-form-item[data-fight-index="${fightIndex}"]`
    );
    if (fightElement) {
        fightElement.remove();
        AppState.eventFights = AppState.eventFights.filter(
            (f) => f.index !== fightIndex
        );
    }
}

// Cria evento
async function handleCreateEvent() {
    try {
        // Coleta dados do formulário
        const name = document.getElementById("eventName").value;
        const date = document.getElementById("eventDate").value;
        const location = document.getElementById("eventLocation").value;
        const organization = document.getElementById("eventOrganization").value;
        const description = document.getElementById("eventDescription").value;

        // Coleta lutas
        const fights = [];
        for (let i = 0; i < AppState.eventFights.length; i++) {
            const fightIndex = AppState.eventFights[i].index;
            const fighter1_id = document.getElementById(
                `fighter1_${fightIndex}`
            ).value;
            const fighter2_id = document.getElementById(
                `fighter2_${fightIndex}`
            ).value;

            if (!fighter1_id || !fighter2_id) {
                showToast(
                    `Selecione ambos os lutadores para a Luta ${fightIndex}`,
                    "warning"
                );
                return;
            }

            fights.push({
                fighter1_id,
                fighter2_id,
                fight_order: fightIndex,
                fight_type: document.getElementById(`fightType_${fightIndex}`)
                    .value,
                rounds: parseInt(
                    document.getElementById(`rounds_${fightIndex}`).value
                ),
                is_title_fight: document.getElementById(`isTitle_${fightIndex}`)
                    .checked,
            });
        }

        if (fights.length === 0) {
            showToast("Adicione pelo menos uma luta ao evento", "warning");
            return;
        }

        showLoading("Criando evento...");

        const eventData = {
            name,
            date,
            location,
            organization,
            description,
            fights,
        };

        await api.createEvent(eventData);

        showToast("Evento criado com sucesso!", "success");

        // Limpa formulário
        document.getElementById("createEventForm").reset();
        document.getElementById("eventFightsContainer").innerHTML = "";
        AppState.eventFights = [];

        // Volta para lista de eventos
        showSection("events");
        await loadEvents();
    } catch (error) {
        showToast(error.message || "Erro ao criar evento", "error");
        console.error(error);
    } finally {
        hideLoading();
    }
}

// Utilitários
function getStatusColor(status) {
    const colors = {
        scheduled: "info",
        completed: "success",
        cancelled: "danger",
    };
    return colors[status] || "secondary";
}

function translateStatus(status) {
    const translations = {
        scheduled: "Agendado",
        completed: "Concluído",
        cancelled: "Cancelado",
    };
    return translations[status] || status;
}

// Filtra eventos
function filterEvents() {
    const status = document.getElementById("eventStatus").value;
    const organization = document.getElementById("eventOrg").value;

    const filters = {};
    if (status) filters.status = status;
    if (organization) filters.organization = organization;

    loadEvents(filters);
}

// Setup event listeners para events
function setupEventsListeners() {
    // Event filters
    const eventStatus = document.getElementById("eventStatus");
    if (eventStatus) {
        eventStatus.addEventListener("change", filterEvents);
    }

    const eventOrg = document.getElementById("eventOrg");
    if (eventOrg) {
        eventOrg.addEventListener("change", filterEvents);
    }

    // Close modal buttons
    const closeModalBtns = document.querySelectorAll(
        "#eventDetailsModal .close, #simulationResultsModal .close"
    );
    closeModalBtns.forEach((btn) => {
        btn.addEventListener("click", (e) => {
            const modal = e.target.closest(".modal");
            if (modal) {
                closeModal(modal.id);
            }
        });
    });
}
