// Events Module - Gerenciamento de eventos de MMA

// Setup events-specific event listeners
function setupEventsListeners() {
    // Event form submit will be set up in setupEventForm()
    // Additional event-specific listeners can be added here
    console.log("Events listeners initialized");
}

// Inicializa a seção de eventos
async function initEventsSection() {
    // Verifica autenticação
    if (!requireAuth()) {
        return;
    }

    try {
        await loadEvents();
        setupEventForm();
    } catch (error) {
        console.error("Erro ao inicializar seção de eventos:", error);

        // Se erro for de autenticação, redireciona para login
        if (
            error.message &&
            (error.message.includes("401") ||
                error.message.includes("Unauthorized"))
        ) {
            showToast("Sessão expirada. Faça login novamente.", "error");
            showSection("login");
        } else {
            showToast("Erro ao carregar eventos", "error");
        }
        hideLoading();
    }
}

// Carrega lista de eventos
async function loadEvents(filters = {}) {
    const eventsList = document.getElementById("eventsList");

    try {
        // Mostra skeleton loading
        eventsList.innerHTML = createSkeletonCards(3, "event");

        const events = await api.getEvents(filters);
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
                (event) => {
                    const orgClass = `org-${event.organization?.toLowerCase().replace(/\s+/g, '-') || 'default'}`;
                    const statusClass = `status-${event.status}`;
                    const dateFormatted = new Date(event.date).toLocaleDateString('pt-BR', {
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric'
                    });

                    return `
                    <div class="event-card-v2 ${orgClass}" data-event-id="${event.id}" onclick="viewEvent('${event.id}')">
                        <div class="event-floating-actions">
                            <button class="btn-icon btn-edit-event" data-event-id="${event.id}" title="Editar evento" onclick="event.stopPropagation(); editEvent('${event.id}')">
                                ✏️
                            </button>
                            <button class="btn-icon btn-delete-event" data-event-id="${event.id}" title="Excluir evento" onclick="event.stopPropagation(); deleteEvent('${event.id}')">
                                🗑️
                            </button>
                        </div>

                        <div class="event-card-body">
                            <div class="event-card-header">
                                <span class="event-org-tag">${escapeHTML(event.organization)}</span>
                                <span class="status-badge ${statusClass}">
                                    ${event.status === 'in_progress' ? '●' : ''} ${translateStatus(event.status)}
                                </span>
                            </div>

                            <h3>${escapeHTML(event.name)}</h3>

                            <div class="event-card-details">
                                <div class="detail-item">
                                    <i>📍</i> ${escapeHTML(event.location || "Local TBA")}
                                </div>
                                <div class="detail-item">
                                    <i>📅</i> ${dateFormatted}
                                </div>
                                <div class="detail-item">
                                    <i>🥊</i> ${event.fights_count || 0} Lutas
                                </div>
                                <div class="detail-item">
                                    <i>🏆</i> Card ${event.status === 'completed' ? 'Finalizado' : 'Proprio'}
                                </div>
                            </div>
                        </div>

                        <div class="event-card-footer">
                            <span class="text-muted" style="font-size: 0.8rem;">ID: #${event.id.substring(0, 8)}</span>
                            ${
                                event.status === "scheduled"
                                    ? `<button class="btn btn-primary btn-sm btn-simulate-event" onclick="event.stopPropagation(); simulateEventClick('${event.id}')">
                                    🎲 Simular Card
                                </button>`
                                    : `<span class="text-success" style="font-weight: 600;">✅ Concluído</span>`
                            }
                        </div>
                    </div>
                `;}
            )
            .join("");
    } catch (error) {
        eventsList.innerHTML = `
            <div class="empty-state">
                <p>❌ Erro ao carregar eventos</p>
                <p class="text-muted">Tente novamente mais tarde</p>
            </div>
        `;
        showToast("Erro ao carregar eventos", "error");
        console.error(error);
    }
}

// Visualiza detalhes de um evento - Now uses dedicated page instead of modal
async function viewEvent(eventId) {
    try {
        showLoading("Carregando evento...");
        AppState.currentEvent = await api.getEvent(eventId);

        // Navigate to event details page
        showSection("eventDetails");

        // Render event details on dedicated page
        showEventDetailsPage(AppState.currentEvent);
    } catch (error) {
        showToast("Erro ao carregar evento", "error");
        console.error(error);
        hideLoading();
    }
}

// Mostra página dedicada com detalhes do evento
function showEventDetailsPage(event) {
    const content = document.getElementById("eventDetailsPageContent");

    const orgClass = `org-${event.organization?.toLowerCase().replace(/\s+/g, '-') || 'default'}`;
    const dateFormatted = new Date(event.date).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: 'long',
        year: 'numeric'
    });

    content.innerHTML = `
        <div class="event-details-page ${orgClass}">
            <div class="event-details-hero">
                <div class="event-details-hero-content">
                    <span class="badge badge-${getStatusColor(event.status)}" style="margin-bottom: 1rem;">
                        ${translateStatus(event.status).toUpperCase()}
                    </span>
                    <h1 class="event-details-title" style="font-size: 3.5rem; font-weight: 800; margin-bottom: 0.5rem;">${escapeHTML(event.name)}</h1>
                    <div class="event-details-meta" style="justify-content: center; gap: 2rem;">
                         <span class="event-meta-item">🏢 <strong>${escapeHTML(event.organization)}</strong></span>
                         <span class="event-meta-item">📅 ${dateFormatted}</span>
                         ${event.location ? `<span class="event-meta-item">📍 ${escapeHTML(event.location)}</span>` : ""}
                    </div>
                </div>
            </div>

            <div class="event-details-content">
                <div class="event-details-main">
                    ${event.description ? `
                        <div class="glass-card" style="padding: 2rem; margin-bottom: 2.5rem; border-radius: 20px;">
                            <h3 style="margin-top: 0; color: var(--primary);">📝 Briefing do Evento</h3>
                            <p style="font-size: 1.1rem; line-height: 1.6; opacity: 0.9;">${escapeHTML(event.description)}</p>
                        </div>` : ""
                    }

                    <div class="event-fights-section">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
                            <h2 style="margin: 0; font-size: 1.8rem;">🥊 Fight Card Oficial</h2>
                            <span class="text-muted">${event.fights?.length || 0} Lutas Confirmadas</span>
                        </div>

                        <div class="fights-list-v2">
                            ${event.fights && event.fights.length > 0
                                ? event.fights
                                    .sort((a, b) => (b.fight_order || 0) - (a.fight_order || 0))
                                    .map((fight) => renderFightCardV2(fight))
                                    .join("")
                                : `<div class="empty-state glass-card" style="padding: 3rem;">
                                     <p>Nenhuma luta casada para este evento ainda.</p>
                                   </div>`
                            }
                        </div>
                    </div>
                </div>

                <div class="event-details-sidebar">
                    <div class="event-actions-card glass-card" style="padding: 2rem; position: sticky; top: 100px; border-radius: 20px;">
                        <h3 style="margin-top: 0; margin-bottom: 1.5rem;">Painel de Controle</h3>
                        <div class="event-actions" style="display: flex; flex-direction: column; gap: 1rem;">
                            ${event.status === "scheduled" ? `
                                <button class="btn btn-primary btn-lg btn-block" id="simulateCurrentEventBtn" style="padding: 1.2rem; font-weight: 700; transform: scale(1.02); box-shadow: 0 4px 15px rgba(210, 10, 10, 0.3);">
                                    🎲 SIMULAR TODO O CARD
                                </button>` : ""
                            }
                            <button class="btn btn-outline btn-block" id="editEventBtn" data-event-id="${event.id}">
                                ✏️ Modificar Evento
                            </button>
                            <div style="height: 1px; background: var(--glass-border); margin: 0.5rem 0;"></div>
                            <button class="btn btn-danger btn-block" id="deleteEventBtn" data-event-id="${event.id}" style="opacity: 0.8;">
                                🗑️ Cancelar/Excluir Evento
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    hideLoading();

    // Setup listeners for action buttons
    setTimeout(() => {
        const simulateBtn = document.getElementById("simulateCurrentEventBtn");
        if (simulateBtn) {
            simulateBtn.addEventListener("click", simulateCurrentEvent);
        }

        const editBtn = document.getElementById("editEventBtn");
        if (editBtn) {
            editBtn.addEventListener("click", () =>
                editEvent(editBtn.dataset.eventId)
            );
        }

        const deleteBtn = document.getElementById("deleteEventBtn");
        if (deleteBtn) {
            deleteBtn.addEventListener("click", () =>
                deleteEvent(deleteBtn.dataset.eventId)
            );
        }
    }, 0);
}

// Keep modal function for backward compatibility
function showEventDetailsModal(event) {
    showEventDetailsPage(event);
}

// Renderiza card de luta premium V2 (Broadcast Visual)
function renderFightCardV2(fight) {
    const isSimulated = fight.status === "simulated";
    const isCompleted = fight.status === "completed";
    const hasResult = isSimulated || isCompleted;

    const getFighterName = (f) => f?.name || "Lutador TBA";
    const getFighterImage = (f) => f?.image_url || 'https://raw.githubusercontent.com/UdsonWillams/fight-base/main/frontend/img/default-fighter.png';

    return `
        <div class="fight-card-v2 ${hasResult ? 'has-result' : ''}">
            <div class="fight-v2-header">
                <span class="fight-order-label">#${fight.fight_order} ${escapeHTML(fight.fight_type.toUpperCase())}</span>
                ${fight.is_title_fight ? '<span class="title-fight-badge">MAIN EVENT / TITLE FIGHT</span>' : ''}
            </div>

            <div class="fight-v2-grid">
                <div class="fighter-v2 red-corner">
                    <img src="${getFighterImage(fight.fighter1)}" class="fighter-v2-avatar">
                    <div class="fighter-v2-info">
                        <span class="fighter-name">${escapeHTML(getFighterName(fight.fighter1))}</span>
                        ${fight.fighter1?.nickname ? `<span class="fighter-nick">"${escapeHTML(fight.fighter1.nickname)}"</span>` : ''}
                    </div>
                </div>

                <div class="fight-v2-vs">
                    <div class="vs-circle">VS</div>
                    <div class="fight-v2-meta">
                        ${fight.rounds} ROUNDS<br>
                        ${fight.weight_class ? escapeHTML(fight.weight_class.toUpperCase().replace('_', ' ')) : ''}
                    </div>
                </div>

                <div class="fighter-v2 blue-corner">
                    <div class="fighter-v2-info">
                        <span class="fighter-name">${escapeHTML(getFighterName(fight.fighter2))}</span>
                        ${fight.fighter2?.nickname ? `<span class="fighter-nick">"${escapeHTML(fight.fighter2.nickname)}"</span>` : ''}
                    </div>
                    <img src="${getFighterImage(fight.fighter2)}" class="fighter-v2-avatar">
                </div>
            </div>

            ${typeof renderMLOdds === 'function' ? renderMLOdds(fight) : ''}

            ${hasResult ? `
                <div class="fight-v2-result">
                    <div class="winner-announcement">
                        VENCEDOR: <span class="winner-name">${fight.winner_id === fight.fighter1_id ? escapeHTML(getFighterName(fight.fighter1)) : escapeHTML(getFighterName(fight.fighter2))}</span>
                    </div>
                    <div class="result-details">
                        ${escapeHTML(fight.result_type)} ${fight.finish_round ? `• Round ${fight.finish_round}` : ''} ${fight.finish_time ? `(${fight.finish_time})` : ''}
                    </div>
                </div>
            ` : `
                <div class="fight-v2-actions">
                    <button class="btn btn-prediction-toggle" onclick="togglePredictionPanel('${fight.id}')">
                        🔮 FAZER PALPITE
                    </button>
                </div>
                <div id="prediction-panel-${fight.id}" class="prediction-panel" style="display: none;">
                    <div class="prediction-title">🔮 SEU PALPITE</div>
                    <div class="prediction-options">
                        <div class="prediction-row">
                            <button class="prediction-btn" onclick="selectPredictionWinner('${fight.id}', '${fight.fighter1_id}')" id="pred-winner-${fight.id}-${fight.fighter1_id}">
                                ${escapeHTML(getFighterName(fight.fighter1))}
                            </button>
                            <button class="prediction-btn" onclick="selectPredictionWinner('${fight.id}', '${fight.fighter2_id}')" id="pred-winner-${fight.id}-${fight.fighter2_id}">
                                ${escapeHTML(getFighterName(fight.fighter2))}
                            </button>
                        </div>
                        <div id="method-options-${fight.id}" style="display: none; margin-top: 10px;">
                            <div class="prediction-title">MÉTODO</div>
                            <select class="form-control" id="pred-method-${fight.id}" style="background: rgba(255,255,255,0.05); color: white; border: 1px solid rgba(255,255,255,0.1);">
                                <option value="">Selecione o método...</option>
                                <option value="KO">KO/TKO</option>
                                <option value="SUB">Submissão</option>
                                <option value="DEC">Decisão</option>
                            </select>

                            <div class="prediction-title" style="margin-top: 10px;">ROUND</div>
                            <div class="prediction-row">
                                ${[1,2,3,4,5].slice(0, fight.rounds).map(r => `
                                    <button class="prediction-btn btn-sm" onclick="selectPredictionRound('${fight.id}', ${r})" id="pred-round-${fight.id}-${r}">
                                        R${r}
                                    </button>
                                `).join('')}
                            </div>
                        </div>
                        <button class="btn btn-primary btn-block" style="margin-top: 15px;" onclick="submitPrediction('${fight.id}', '${fight.event_id}')">
                            CONFIRMAR PALPITE
                        </button>
                    </div>
                </div>
            `}
        </div>
    `;
}

// Prediction UI Functions
function togglePredictionPanel(fightId) {
    const panel = document.getElementById(`prediction-panel-${fightId}`);
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
}

function selectPredictionWinner(fightId, fighterId) {
    // UI selection logic
    const btns = document.querySelectorAll(`[id^="pred-winner-${fightId}"]`);
    btns.forEach(b => b.classList.remove('selected'));
    document.getElementById(`pred-winner-${fightId}-${fighterId}`).classList.add('selected');

    // Show method/round options
    document.getElementById(`method-options-${fightId}`).style.display = 'block';

    // Store in temp state
    if (!window.tempPredictions) window.tempPredictions = {};
    window.tempPredictions[fightId] = { ...(window.tempPredictions[fightId] || {}), winner_id: fighterId };
}

function selectPredictionRound(fightId, round) {
    const btns = document.querySelectorAll(`[id^="pred-round-${fightId}"]`);
    btns.forEach(b => b.classList.remove('selected'));
    document.getElementById(`pred-round-${fightId}-${round}`).classList.add('selected');

    if (!window.tempPredictions) window.tempPredictions = {};
    window.tempPredictions[fightId] = { ...(window.tempPredictions[fightId] || {}), round: round };
}

async function submitPrediction(fightId, eventId) {
    const pred = window.tempPredictions?.[fightId];
    const method_code = document.getElementById(`pred-method-${fightId}`).value;

    if (!pred || !pred.winner_id) {
        showToast("Selecione o vencedor!", "warning");
        return;
    }

    if (!method_code) {
        showToast("Selecione o método!", "warning");
        return;
    }

    try {
        showLoading("Salvando palpite...");

        // Em um sistema real, buscaríamos o ID do FinishMethod baseado no código (KO, SUB, DEC)
        // Por enquanto, enviaremos apenas o que temos e o backend ou o api.js resolvem
        await api.createPrediction({
            fight_id: fightId,
            event_id: eventId,
            predicted_winner_id: pred.winner_id,
            predicted_method_code: method_code, // Ajustado para facilidade
            predicted_round: pred.round
        });

        showToast("Palpite registrado com sucesso! 🔮", "success");
        togglePredictionPanel(fightId);

        // Desabilitar botão ou mudar UI
        const toggleBtn = document.querySelector(`button[onclick="togglePredictionPanel('${fightId}')"]`);
        if (toggleBtn) {
            toggleBtn.innerHTML = "✅ PALPITE REGISTRADO";
            toggleBtn.disabled = true;
        }
    } catch (error) {
        showToast("Erro ao salvar palpite", "error");
        console.error(error);
    } finally {
        hideLoading();
    }
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
    const isCompleted = fight.status === "completed";
    const hasResult = isSimulated || isCompleted;

    return `
        <div class="fight-card ${isSimulated ? "simulated" : ""} ${
        isCompleted ? "completed" : ""
    }">
            <div class="fight-order">
                #${fight.fight_order || "?"} ${escapeHTML(getFightTypeLabel(
        fight.fight_type
    ))}
                ${
                    fight.is_title_fight
                        ? ' <span class="badge badge-warning">Luta de Título</span>'
                        : ""
                }
            </div>

            <div class="fight-matchup">
                <div class="fighter-info">
                    <strong>${escapeHTML(fight.fighter1?.name || "Fighter 1")}</strong>
                    ${
                        fight.fighter1?.nickname
                            ? `<span class="nickname">"${escapeHTML(fight.fighter1.nickname)}"</span>`
                            : ""
                    }
                    ${
                        hasResult && fight.winner_id === fight.fighter1_id
                            ? ' <span class="winner-badge">🏆 WIN</span>'
                            : ""
                    }
                </div>

                <div class="vs">VS</div>

                <div class="fighter-info">
                    <strong>${escapeHTML(fight.fighter2?.name || "Fighter 2")}</strong>
                    ${
                        fight.fighter2?.nickname
                            ? `<span class="nickname">"${escapeHTML(fight.fighter2.nickname)}"</span>`
                            : ""
                    }
                    ${
                        hasResult && fight.winner_id === fight.fighter2_id
                            ? ' <span class="winner-badge">🏆 WIN</span>'
                            : ""
                    }
                </div>
            </div>

            ${
                hasResult
                    ? `
                <div class="fight-result">
                    <p><strong>Resultado:</strong> ${escapeHTML(fight.result_type)}${
                          fight.finish_round
                              ? ` - Round ${fight.finish_round}`
                              : ""
                      }${fight.finish_time ? ` (${fight.finish_time})` : ""}</p>
                    ${
                        fight.method_details
                            ? `<p><strong>Método:</strong> ${escapeHTML(fight.method_details)}</p>`
                            : ""
                    }
                    <p><strong>Probabilidades:</strong> ${
                        escapeHTML(fight.fighter1?.name)
                    } ${fight.fighter1_probability}% vs ${
                          escapeHTML(fight.fighter2?.name)
                      } ${fight.fighter2_probability}%</p>
                </div>
            `
                    : ""
            }

            <div class="fight-meta">
                <span>${fight.rounds} rounds</span>
                ${
                    fight.weight_class
                        ? `<span>${escapeHTML(fight.weight_class)}</span>`
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

// Editar evento
async function editEvent(eventId) {
    try {
        showLoading("Carregando evento...");
        const event = await api.getEvent(eventId);

        // Fecha o modal de detalhes se estiver aberto
        closeModal("eventDetailsModal");

        // Vai para a seção de editar evento (página dedicada)
        showSection("editEvent");

        // Aguarda um pouco para garantir que o DOM foi atualizado
        await new Promise((resolve) => setTimeout(resolve, 200));

        // Preenche o formulário de edição com os dados do evento
        const eventNameEl = document.getElementById("editEventName");
        const eventDateEl = document.getElementById("editEventDate");
        const eventOrgEl = document.getElementById("editEventOrganization");
        const eventLocEl = document.getElementById("editEventLocation");
        const eventDescEl = document.getElementById("editEventDescription");

        if (
            !eventNameEl ||
            !eventDateEl ||
            !eventOrgEl ||
            !eventLocEl ||
            !eventDescEl
        ) {
            throw new Error("Elementos do formulário não encontrados");
        }

        eventNameEl.value = event.name;

        // Converte a data para o formato correto (YYYY-MM-DD)
        const eventDate = new Date(event.date);
        const formattedDate = eventDate.toISOString().split("T")[0];
        eventDateEl.value = formattedDate;

        eventOrgEl.value = event.organization;
        eventLocEl.value = event.location || "";
        eventDescEl.value = event.description || "";

        // Armazena o ID do evento sendo editado
        AppState.editingEventId = eventId;

        // Limpa e preenche as lutas (usa o container de edição)
        AppState.eventFights = [];
        const fightsContainer = document.getElementById(
            "editEventFightsContainer"
        );
        if (!fightsContainer) {
            throw new Error("Container de lutas de edição não encontrado");
        }
        fightsContainer.innerHTML = "";

        // Função auxiliar para preencher uma luta após ser adicionada ao DOM
        const fillFightData = async (fightIndex, fight) => {
            // Aguarda mais tempo para garantir que o DOM foi atualizado completamente
            await new Promise((resolve) => setTimeout(resolve, 200));

            // Tenta encontrar os elementos, com retry se necessário
            let attempts = 0;
            const maxAttempts = 20; // Aumentado para dar mais tempo

            const findAndFill = () => {
                console.log(
                    `Tentativa ${
                        attempts + 1
                    }: Procurando elementos da luta ${fightIndex}`
                );
                const fightTypeEl = document.getElementById(
                    `fightType_${fightIndex}`
                );
                const roundsEl = document.getElementById(
                    `rounds_${fightIndex}`
                );
                const isTitleEl = document.getElementById(
                    `isTitle_${fightIndex}`
                );
                const fighter1El = document.getElementById(
                    `fighter1_${fightIndex}`
                );
                const fighter2El = document.getElementById(
                    `fighter2_${fightIndex}`
                );
                const fighter1Input = document.querySelector(
                    `input.fighter-search[data-fight="${fightIndex}"][data-fighter="1"]`
                );
                const fighter2Input = document.querySelector(
                    `input.fighter-search[data-fight="${fightIndex}"][data-fighter="2"]`
                );

                // Debug: verifica quais elementos foram encontrados
                const foundElements = {
                    fightTypeEl: !!fightTypeEl,
                    roundsEl: !!roundsEl,
                    isTitleEl: !!isTitleEl,
                    fighter1El: !!fighter1El,
                    fighter2El: !!fighter2El,
                    fighter1Input: !!fighter1Input,
                    fighter2Input: !!fighter2Input,
                };

                if (attempts === 0) {
                    console.log(
                        `Elementos encontrados para luta ${fightIndex}:`,
                        foundElements
                    );
                }

                // Se todos os elementos principais existem, preenche
                if (
                    fightTypeEl &&
                    roundsEl &&
                    isTitleEl &&
                    fighter1El &&
                    fighter2El
                ) {
                    // Preenche os campos
                    fightTypeEl.value = fight.fight_type || "standard";
                    roundsEl.value = String(fight.rounds || 3);

                    // Corrige o checkbox - garante que está marcado/desmarcado corretamente
                    const shouldBeChecked = Boolean(fight.is_title_fight);

                    console.log(`Checkbox luta ${fightIndex}:`, {
                        shouldBeChecked,
                        originalValue: fight.is_title_fight,
                        element: isTitleEl,
                    });

                    // Remove o atributo checked primeiro para garantir estado limpo
                    isTitleEl.removeAttribute("checked");
                    isTitleEl.checked = false;

                    // Se deve estar marcado, marca
                    if (shouldBeChecked) {
                        isTitleEl.setAttribute("checked", "checked");
                        isTitleEl.checked = true;
                    }

                    // Força atualização visual com múltiplas abordagens
                    isTitleEl.dispatchEvent(
                        new Event("input", { bubbles: true })
                    );
                    isTitleEl.dispatchEvent(
                        new Event("change", { bubbles: true })
                    );

                    // Usa requestAnimationFrame para garantir que o DOM foi atualizado
                    requestAnimationFrame(() => {
                        isTitleEl.checked = shouldBeChecked;
                        if (shouldBeChecked) {
                            isTitleEl.setAttribute("checked", "checked");
                        } else {
                            isTitleEl.removeAttribute("checked");
                        }
                    });

                    // Preenche os IDs dos lutadores
                    fighter1El.value = String(fight.fighter1_id || "");
                    fighter2El.value = String(fight.fighter2_id || "");

                    // Preenche os nomes nos inputs de busca
                    // A API retorna fighter1 e fighter2 como objetos, não fighter1_name
                    const fighter1Name = fight.fighter1?.name || "";
                    const fighter2Name = fight.fighter2?.name || "";

                    console.log(`Preenchendo luta ${fightIndex}:`, {
                        fighter1Name,
                        fighter2Name,
                        fighter1Input: !!fighter1Input,
                        fighter2Input: !!fighter2Input,
                        isTitleEl: !!isTitleEl,
                        shouldBeChecked,
                    });

                    if (fighter1Input && fighter1Name) {
                        fighter1Input.value = fighter1Name;
                        console.log(
                            `Fighter1 input preenchido: ${fighter1Name}`
                        );
                    }
                    if (fighter2Input && fighter2Name) {
                        fighter2Input.value = fighter2Name;
                        console.log(
                            `Fighter2 input preenchido: ${fighter2Name}`
                        );
                    }

                    // setupFighterSearchForFight já é chamado em addFightToForm(), não precisa chamar novamente

                    return true;
                }

                return false;
            };

            // Tenta preencher, com retry se necessário
            while (attempts < maxAttempts) {
                if (findAndFill()) {
                    console.log(
                        `✅ Luta ${fightIndex} preenchida com sucesso na tentativa ${
                            attempts + 1
                        }`
                    );
                    return true;
                }
                attempts++;
                await new Promise((resolve) => setTimeout(resolve, 100)); // Aumentado para 100ms
            }

            console.error(
                `❌ Falha ao preencher luta ${fightIndex} após ${maxAttempts} tentativas`
            );
            return false;
        };

        // Adiciona todas as lutas sequencialmente
        if (event.fights && event.fights.length > 0) {
            console.log("Carregando lutas para edição:", event.fights);

            for (let index = 0; index < event.fights.length; index++) {
                const fight = event.fights[index];

                // O fightIndex é baseado no tamanho atual do array + 1 (1-based)
                const fightIndex = AppState.eventFights.length + 1;

                // Extrai os nomes dos lutadores corretamente
                const fighter1Name = fight.fighter1?.name || "";
                const fighter2Name = fight.fighter2?.name || "";

                console.log(`Luta ${fightIndex}:`, {
                    fighter1_id: fight.fighter1_id,
                    fighter1_name: fighter1Name,
                    fighter2_id: fight.fighter2_id,
                    fighter2_name: fighter2Name,
                    fight_type: fight.fight_type,
                    rounds: fight.rounds,
                    is_title_fight: fight.is_title_fight,
                });

                // Renderiza a luta no formulário de edição PRIMEIRO (com o índice correto)
                addFightToEditForm(fightIndex);

                // Adiciona a luta ao estado DEPOIS de renderizar
                AppState.eventFights.push({
                    index: fightIndex,
                    fighter1_id: fight.fighter1_id,
                    fighter2_id: fight.fighter2_id,
                    fighter1_name: fighter1Name,
                    fighter2_name: fighter2Name,
                    fight_type: fight.fight_type || "standard",
                    rounds: fight.rounds || 3,
                    is_title_fight: Boolean(fight.is_title_fight),
                });

                // Aguarda mais tempo para garantir que o DOM foi atualizado
                await new Promise((resolve) => setTimeout(resolve, 150));

                // Preenche os dados da luta
                const filled = await fillFightData(fightIndex, fight);

                if (!filled) {
                    console.warn(
                        `Aviso: Luta ${fightIndex} pode não ter sido preenchida completamente`
                    );
                }
            }
        }

        // Aguarda um pouco mais para garantir que tudo foi renderizado
        await new Promise((resolve) => setTimeout(resolve, 100));

        hideLoading();

        showToast("Evento carregado para edição", "success");

        // Scroll para o topo da página
        window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (error) {
        showToast("Erro ao carregar evento para edição", "error");
        console.error(error);
        hideLoading();
    }
}

// Excluir evento
async function deleteEvent(eventId) {
    const confirmed = await showConfirm(
        "Tem certeza que deseja excluir este evento?",
        "Esta ação não pode ser desfeita."
    );

    if (!confirmed) return;

    try {
        showLoading("Excluindo evento...");
        await api.deleteEvent(eventId);

        showToast("Evento excluído com sucesso!", "success");

        // Volta para lista e recarrega
        showSection("events");
        await loadEvents();
    } catch (error) {
        showToast("Erro ao excluir evento", "error");
        console.error(error);
    } finally {
        hideLoading();
    }
}

// Reseta o formulário de eventos
function resetEventForm() {
    document.getElementById("createEventForm").reset();
    document.getElementById("eventFightsContainer").innerHTML = "";
    AppState.eventFights = [];
    AppState.editingEventId = null;

    // Restaura o texto do botão
    const submitBtn = document.querySelector(
        "#createEventForm button[type='submit']"
    );
    if (submitBtn) {
        submitBtn.innerHTML = "✅ Criar Evento";
    }
}

// Simula evento atual (da página ou modal)
async function simulateCurrentEvent() {
    if (!AppState.currentEvent) return;
    await simulateEventClick(AppState.currentEvent.id);
    // Reload event details page
    await viewEvent(AppState.currentEvent.id);
}

// Mostra resultados da simulação
function showSimulationResults(result) {
    const modal = document.getElementById("simulationResultsModal");
    const content = document.getElementById("simulationResultsContent");

    content.innerHTML = `
        <div class="simulation-results">
            <h2>🎉 ${escapeHTML(result.event_name)} - Resultados</h2>

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
let eventFormInitialized = false;

function setupEventForm() {
    // Evita adicionar listeners múltiplas vezes
    if (eventFormInitialized) {
        return;
    }

    const form = document.getElementById("createEventForm");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        await handleCreateEvent();
    });

    // Auto-save functionality
    let autoSaveTimeout;
    const autoSaveDelay = 2000; // 2 segundos após parar de digitar

    const formInputs = form.querySelectorAll(
        'input[type="text"], input[type="date"], select, textarea'
    );
    formInputs.forEach((input) => {
        input.addEventListener("input", () => {
            clearTimeout(autoSaveTimeout);
            autoSaveTimeout = setTimeout(() => {
                saveFormDraft();
            }, autoSaveDelay);
        });
    });

    // Carrega rascunho salvo ao iniciar
    loadFormDraft();

    // Botão para adicionar luta
    const addFightBtn = document.getElementById("addFightBtn");
    if (addFightBtn) {
        addFightBtn.addEventListener("click", addFightToForm);
    }

    // Event delegation for remove fight buttons
    const fightsContainer = document.getElementById("eventFightsContainer");
    if (fightsContainer) {
        fightsContainer.addEventListener("click", (e) => {
            const removeBtn = e.target.closest(".btn-remove-fight");
            if (removeBtn) {
                const fightIndex = parseInt(removeBtn.dataset.fightIndex);
                if (fightIndex) {
                    removeFight(fightIndex);
                }
            }
        });
    }

    eventFormInitialized = true;
}

// Salva rascunho do formulário no localStorage
function saveFormDraft() {
    try {
        const form = document.getElementById("createEventForm");
        if (!form) return;

        // Se estiver editando um evento, não salva rascunho
        if (AppState.editingEventId) return;

        const draft = {
            name: document.getElementById("eventName")?.value || "",
            date: document.getElementById("eventDate")?.value || "",
            location: document.getElementById("eventLocation")?.value || "",
            organization:
                document.getElementById("eventOrganization")?.value || "",
            status:
                document.getElementById("eventStatus")?.value || "scheduled",
            savedAt: new Date().toISOString(),
        };

        localStorage.setItem("eventFormDraft", JSON.stringify(draft));

        // Mostra indicador visual de salvamento
        const saveIndicator = document.getElementById("autoSaveIndicator");
        if (saveIndicator) {
            saveIndicator.textContent = "💾 Salvo automaticamente";
            saveIndicator.style.display = "block";
            setTimeout(() => {
                saveIndicator.style.display = "none";
            }, 2000);
        }
    } catch (error) {
        console.error("Erro ao salvar rascunho:", error);
    }
}

// Carrega rascunho do formulário do localStorage
function loadFormDraft() {
    try {
        const draftJson = localStorage.getItem("eventFormDraft");
        if (!draftJson) return;

        const draft = JSON.parse(draftJson);

        // Verifica se o rascunho não é muito antigo (mais de 7 dias)
        const savedDate = new Date(draft.savedAt);
        const daysDiff =
            (Date.now() - savedDate.getTime()) / (1000 * 60 * 60 * 24);

        if (daysDiff > 7) {
            localStorage.removeItem("eventFormDraft");
            return;
        }

        // Preenche o formulário
        if (draft.name) document.getElementById("eventName").value = draft.name;
        if (draft.date) document.getElementById("eventDate").value = draft.date;
        if (draft.location)
            document.getElementById("eventLocation").value = draft.location;
        if (draft.organization)
            document.getElementById("eventOrganization").value =
                draft.organization;
        if (draft.status)
            document.getElementById("eventStatus").value = draft.status;

        showToast("Rascunho restaurado automaticamente", "info");
    } catch (error) {
        console.error("Erro ao carregar rascunho:", error);
        localStorage.removeItem("eventFormDraft");
    }
}

// Limpa rascunho do localStorage
function clearFormDraft() {
    localStorage.removeItem("eventFormDraft");
}

// Adiciona luta ao formulário de edição
function addFightToEditForm(customFightIndex = null) {
    const fightsContainer = document.getElementById("editEventFightsContainer");
    if (!fightsContainer) return;

    const fightIndex = customFightIndex !== null ? customFightIndex : AppState.eventFights.length + 1;

    const fightHtml = `
        <div class="card-builder-item" data-fight-index="${fightIndex}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                <h4 style="margin: 0; color: var(--primary);">Luta #${fightIndex}</h4>
                <button type="button" class="btn btn-icon btn-remove-fight" data-fight-index="${fightIndex}" title="Remover Luta">
                    🗑️
                </button>
            </div>

            <div class="form-row">
                <div class="form-group" style="position: relative;">
                    <label>Córner Vermelho</label>
                    <input type="text" class="fighter-search" data-fight="${fightIndex}" data-fighter="1" placeholder="🔍 Buscar lutador...">
                    <div class="search-results" id="searchResults_${fightIndex}_1"></div>
                    <input type="hidden" id="fighter1_${fightIndex}">
                </div>

                <div class="form-group" style="position: relative;">
                    <label>Córner Azul</label>
                    <input type="text" class="fighter-search" data-fight="${fightIndex}" data-fighter="2" placeholder="🔍 Buscar lutador...">
                    <div class="search-results" id="searchResults_${fightIndex}_2"></div>
                    <input type="hidden" id="fighter2_${fightIndex}">
                </div>
            </div>

            <div class="form-row" style="margin-top: 1rem;">
                <div class="form-group">
                    <label>Nível do Card</label>
                    <select id="fightType_${fightIndex}">
                        <option value="standard">Fight Card</option>
                        <option value="prelim">Prelim</option>
                        <option value="co-main">Co-Main Event</option>
                        <option value="main">Main Event</option>
                    </select>
                </div>

                <div class="form-group" style="max-width: 120px;">
                    <label>Rounds</label>
                    <select id="rounds_${fightIndex}">
                        <option value="3">3</option>
                        <option value="5">5</option>
                    </select>
                </div>

                <div class="form-group" style="display: flex; align-items: center; gap: 0.8rem; padding-top: 1.8rem;">
                    <input type="checkbox" id="isTitle_${fightIndex}" style="width: 20px; height: 20px; cursor: pointer;">
                    <label for="isTitle_${fightIndex}" style="margin: 0; cursor: pointer;">Disputa de Título</label>
                </div>
            </div>
        </div>
    `;

    fightsContainer.insertAdjacentHTML("beforeend", fightHtml);

    if (customFightIndex === null) {
        const existingFight = AppState.eventFights.find((f) => f.index === fightIndex);
        if (!existingFight) AppState.eventFights.push({ index: fightIndex });
    }

    setupFighterSearchForFight(fightIndex);
}

// Adiciona luta ao formulário (criação)
function addFightToForm(customFightIndex = null) {
    const fightsContainer = document.getElementById("eventFightsContainer");
    if (!fightsContainer) return;

    const fightIndex = customFightIndex !== null ? customFightIndex : AppState.eventFights.length + 1;

    const fightHtml = `
        <div class="card-builder-item" data-fight-index="${fightIndex}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                <h4 style="margin: 0; color: var(--primary);">Luta #${fightIndex}</h4>
                <button type="button" class="btn btn-icon btn-remove-fight" data-fight-index="${fightIndex}" title="Remover Luta">
                    🗑️
                </button>
            </div>

            <div class="form-row">
                <div class="form-group" style="position: relative;">
                    <label>Córner Vermelho</label>
                    <input type="text" class="fighter-search" data-fight="${fightIndex}" data-fighter="1" placeholder="🔍 Buscar lutador...">
                    <div class="search-results" id="searchResults_${fightIndex}_1"></div>
                    <input type="hidden" id="fighter1_${fightIndex}">
                </div>

                <div class="form-group" style="position: relative;">
                    <label>Córner Azul</label>
                    <input type="text" class="fighter-search" data-fight="${fightIndex}" data-fighter="2" placeholder="🔍 Buscar lutador...">
                    <div class="search-results" id="searchResults_${fightIndex}_2"></div>
                    <input type="hidden" id="fighter2_${fightIndex}">
                </div>
            </div>

            <div class="form-row" style="margin-top: 1rem;">
                <div class="form-group">
                    <label>Nível do Card</label>
                    <select id="fightType_${fightIndex}">
                        <option value="standard">Fight Card</option>
                        <option value="prelim">Prelim</option>
                        <option value="co-main">Co-Main Event</option>
                        <option value="main">Main Event</option>
                    </select>
                </div>

                <div class="form-group" style="max-width: 120px;">
                    <label>Rounds</label>
                    <select id="rounds_${fightIndex}">
                        <option value="3">3</option>
                        <option value="5">5</option>
                    </select>
                </div>

                <div class="form-group" style="display: flex; align-items: center; gap: 0.8rem; padding-top: 1.8rem;">
                    <input type="checkbox" id="isTitle_${fightIndex}" style="width: 20px; height: 20px; cursor: pointer;">
                    <label for="isTitle_${fightIndex}" style="margin: 0; cursor: pointer;">Disputa de Título</label>
                </div>
            </div>
        </div>
    `;

    fightsContainer.insertAdjacentHTML("beforeend", fightHtml);

    if (customFightIndex === null) {
        const existingFight = AppState.eventFights.find((f) => f.index === fightIndex);
        if (!existingFight) AppState.eventFights.push({ index: fightIndex });
    }

    setupFighterSearchForFight(fightIndex);
}

// Setup busca de lutadores para uma luta
function setupFighterSearchForFight(fightIndex) {
    const inputs = document.querySelectorAll(
        `input.fighter-search[data-fight="${fightIndex}"]`
    );

    // Event delegation for search results
    const resultsDiv1 = document.getElementById(
        `searchResults_${fightIndex}_1`
    );
    const resultsDiv2 = document.getElementById(
        `searchResults_${fightIndex}_2`
    );

    [resultsDiv1, resultsDiv2].forEach((resultsDiv) => {
        if (resultsDiv) {
            resultsDiv.addEventListener("click", (e) => {
                const resultItem = e.target.closest(".search-result-item");
                if (resultItem) {
                    const fighterId = resultItem.dataset.fighterId;
                    const fighterName = resultItem.dataset.fighterName;
                    const fightIdx = parseInt(resultItem.dataset.fightIndex);
                    const fighterNum = parseInt(resultItem.dataset.fighterNum);

                    if (fighterId && fighterName && fightIdx && fighterNum) {
                        selectFighterForEvent(
                            fightIdx,
                            fighterNum,
                            fighterId,
                            fighterName
                        );
                    }
                }
            });
        }
    });

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
        <div class="search-result-item"
             data-fighter-id="${fighter.id}"
             data-fighter-name="${fighter.name.replace(/"/g, "&quot;")}"
             data-fight-index="${fightIndex}"
             data-fighter-num="${fighterNum}">
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

// Remove luta do formulário (funciona para ambos: criação e edição)
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

// Handler para salvar edição de evento
async function handleEditEvent() {
    try {
        if (!AppState.editingEventId) {
            showToast("Nenhum evento sendo editado", "error");
            return;
        }

        // Coleta dados do formulário de edição
        const nameEl = document.getElementById("editEventName");
        const dateEl = document.getElementById("editEventDate");
        const locationEl = document.getElementById("editEventLocation");
        const organizationEl = document.getElementById("editEventOrganization");
        const descriptionEl = document.getElementById("editEventDescription");

        if (
            !nameEl ||
            !dateEl ||
            !locationEl ||
            !organizationEl ||
            !descriptionEl
        ) {
            showToast("Erro: elementos do formulário não encontrados", "error");
            return;
        }

        const name = nameEl.value;
        const date = dateEl.value;
        const location = locationEl.value;
        const organization = organizationEl.value;
        const description = descriptionEl.value;

        // Coleta lutas do container de edição
        const fights = [];
        for (let i = 0; i < AppState.eventFights.length; i++) {
            const fightIndex = AppState.eventFights[i].index;
            const fighter1El = document.getElementById(
                `fighter1_${fightIndex}`
            );
            const fighter2El = document.getElementById(
                `fighter2_${fightIndex}`
            );
            const fightTypeEl = document.getElementById(
                `fightType_${fightIndex}`
            );
            const roundsEl = document.getElementById(`rounds_${fightIndex}`);
            const isTitleEl = document.getElementById(`isTitle_${fightIndex}`);

            if (
                !fighter1El ||
                !fighter2El ||
                !fightTypeEl ||
                !roundsEl ||
                !isTitleEl
            ) {
                console.warn(`Elementos da luta ${fightIndex} não encontrados`);
                continue;
            }

            const fighter1_id = fighter1El.value;
            const fighter2_id = fighter2El.value;

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
                fight_type: fightTypeEl.value,
                rounds: parseInt(roundsEl.value),
                is_title_fight: isTitleEl.checked,
            });
        }

        if (fights.length === 0) {
            showToast("Adicione pelo menos uma luta ao evento", "warning");
            return;
        }

        const eventData = {
            name,
            date,
            location,
            organization,
            description,
            fights,
        };

        showLoading("Atualizando evento...");
        await api.updateEvent(AppState.editingEventId, eventData);
        showToast("Evento atualizado com sucesso!", "success");

        // Limpa estado
        AppState.editingEventId = null;
        AppState.eventFights = [];

        // Volta para lista de eventos
        showSection("events");
        await loadEvents();
    } catch (error) {
        showToast(error.message || "Erro ao atualizar evento", "error");
        console.error(error);
    } finally {
        hideLoading();
    }
}

// Cria evento
async function handleCreateEvent() {
    try {
        // Coleta dados do formulário
        const nameEl = document.getElementById("eventName");
        const dateEl = document.getElementById("eventDate");
        const locationEl = document.getElementById("eventLocation");
        const organizationEl = document.getElementById("eventOrganization");
        const descriptionEl = document.getElementById("eventDescription");

        // Verifica se todos os elementos existem
        if (
            !nameEl ||
            !dateEl ||
            !locationEl ||
            !organizationEl ||
            !descriptionEl
        ) {
            console.error("Elementos do formulário não encontrados");
            return;
        }

        const name = nameEl.value;
        const date = dateEl.value;
        const location = locationEl.value;
        const organization = organizationEl.value;
        const description = descriptionEl.value;

        // Coleta lutas
        const fights = [];
        for (let i = 0; i < AppState.eventFights.length; i++) {
            const fightIndex = AppState.eventFights[i].index;
            const fighter1El = document.getElementById(
                `fighter1_${fightIndex}`
            );
            const fighter2El = document.getElementById(
                `fighter2_${fightIndex}`
            );
            const fightTypeEl = document.getElementById(
                `fightType_${fightIndex}`
            );
            const roundsEl = document.getElementById(`rounds_${fightIndex}`);
            const isTitleEl = document.getElementById(`isTitle_${fightIndex}`);

            // Verifica se os elementos existem
            if (
                !fighter1El ||
                !fighter2El ||
                !fightTypeEl ||
                !roundsEl ||
                !isTitleEl
            ) {
                console.error(
                    `Elementos da luta ${fightIndex} não encontrados`
                );
                continue;
            }

            const fighter1_id = fighter1El.value;
            const fighter2_id = fighter2El.value;

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
                fight_type: fightTypeEl.value,
                rounds: parseInt(roundsEl.value),
                is_title_fight: isTitleEl.checked,
            });
        }

        if (fights.length === 0) {
            showToast("Adicione pelo menos uma luta ao evento", "warning");
            return;
        }

        const eventData = {
            name,
            date,
            location,
            organization,
            description,
            fights,
        };

        // Cria o evento (edição agora tem handler separado)
        showLoading("Criando evento...");
        await api.createEvent(eventData);
        showToast("Evento criado com sucesso!", "success");
        clearFormDraft(); // Limpa o rascunho após criar com sucesso

        // Limpa formulário
        document.getElementById("createEventForm").reset();
        document.getElementById("eventFightsContainer").innerHTML = "";
        AppState.eventFights = [];

        // Restaura o texto do botão
        const submitBtn = document.querySelector(
            "#createEventForm button[type='submit']"
        );
        if (submitBtn) {
            submitBtn.innerHTML = "✅ Criar Evento";
        }

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
        in_progress: "warning",
        completed: "success",
        cancelled: "danger",
    };
    return colors[status] || "secondary";
}

function translateStatus(status) {
    const translations = {
        scheduled: "🗓️ Agendado",
        in_progress: "▶️ Em Andamento",
        completed: "✅ Concluído",
        cancelled: "❌ Cancelado",
    };
    return translations[status] || status;
}

// Filtra eventos
function filterEvents() {
    const search = document.getElementById("eventSearch").value;
    const status = document.getElementById("eventStatus").value;
    const organization = document.getElementById("eventOrg").value;
    const orderBy = document.getElementById("eventOrderBy").value;

    const filters = {};
    if (search) filters.search = search;
    if (status) filters.status = status;
    if (organization) filters.organization = organization;
    if (orderBy) filters.order_by = orderBy;

    loadEvents(filters);
}

// Setup event listeners para events
let eventsListenersInitialized = false;

function setupEventsListeners() {
    // Evita adicionar listeners múltiplas vezes
    if (eventsListenersInitialized) {
        return;
    }

    // Event delegation for event cards and action buttons
    const eventsList = document.getElementById("eventsList");
    if (eventsList) {
        eventsList.addEventListener("click", (e) => {
            // Check if clicked on edit button
            const editBtn = e.target.closest(".btn-edit-event");
            if (editBtn) {
                e.stopPropagation();
                const eventId = editBtn.dataset.eventId;
                if (eventId) {
                    editEvent(eventId);
                }
                return;
            }

            // Check if clicked on delete button
            const deleteBtn = e.target.closest(".btn-delete-event");
            if (deleteBtn) {
                e.stopPropagation();
                const eventId = deleteBtn.dataset.eventId;
                if (eventId) {
                    deleteEvent(eventId);
                }
                return;
            }

            // Check if clicked on simulate button
            const simulateBtn = e.target.closest(".btn-simulate-event");
            if (simulateBtn) {
                e.stopPropagation();
                const eventId = simulateBtn.dataset.eventId;
                if (eventId) {
                    simulateEventClick(eventId);
                }
                return;
            }

            // Otherwise check if clicked on event card
            const eventCard = e.target.closest(".event-card");
            if (eventCard) {
                const eventId = eventCard.dataset.eventId;
                if (eventId) {
                    viewEvent(eventId);
                }
            }
        });
    }

    // Event filters
    const eventSearch = document.getElementById("eventSearch");
    if (eventSearch) {
        let searchTimeout;
        eventSearch.addEventListener("input", () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(filterEvents, 300);
        });
    }

    const eventStatus = document.getElementById("eventStatus");
    if (eventStatus) {
        eventStatus.addEventListener("change", filterEvents);
    }

    const eventOrg = document.getElementById("eventOrg");
    if (eventOrg) {
        eventOrg.addEventListener("change", filterEvents);
    }

    const eventOrderBy = document.getElementById("eventOrderBy");
    if (eventOrderBy) {
        eventOrderBy.addEventListener("change", filterEvents);
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

    eventsListenersInitialized = true;
}
