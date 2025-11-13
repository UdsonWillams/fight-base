// Fighters Module - v1.1

// Helper function to get overall rating
function getOverall(fighter) {
    // Se tiver overall rating, usa
    if (fighter.overall_rating || fighter.overall) {
        return fighter.overall_rating || fighter.overall;
    }

    // Calcula baseado nos atributos (deprecated mas ainda presentes)
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
            // Pega a média dos 4 maiores atributos (ignora os 2 mais fracos)
            attrs.sort((a, b) => b - a);
            const top4 = attrs.slice(0, 4);
            return top4.reduce((a, b) => a + b, 0) / top4.length;
        }
    }

    // Fallback: baseado no record
    const wins = fighter.wins || 0;
    const losses = fighter.losses || 0;
    const total = wins + losses;

    if (total > 0) {
        const winRate = wins / total;
        return 60 + winRate * 35; // 60-95 range based on win rate
    }

    return 75; // Default
}

// Load fighters list
async function loadFighters(filters = {}) {
    const container = document.getElementById("fightersList");

    try {
        // Mostra skeleton loading
        container.innerHTML = createSkeletonCards(6, "fighter");

        const params = {
            limit: 50,
            offset: 0,
            ...filters,
        };

        const response = await api.getFighters(params);
        AppState.allFighters = response.fighters || [];

        displayFighters(AppState.allFighters);
    } catch (error) {
        container.innerHTML = `
            <div class="empty-state">
                <p>❌ Erro ao carregar lutadores</p>
                <p class="text-muted">Tente novamente mais tarde</p>
            </div>
        `;
        console.error("Error loading fighters:", error);
        showToast("Erro ao carregar lutadores", "error");
    }
}

// Create fighter card from template
function createFighterCard(fighter) {
    const template = document.getElementById("fighter-card-template");
    const card = template.content.cloneNode(true);

    // Get elements
    const cardEl = card.querySelector(".fighter-card");
    const imageEl = card.querySelector(".fighter-image");
    const nameEl = card.querySelector(".fighter-name");
    const nicknameEl = card.querySelector(".fighter-nickname");
    const metaEl = card.querySelector(".fighter-meta");

    // Set data attribute
    cardEl.dataset.fighterId = fighter.id;

    // Set image
    if (fighter.photo_url) {
        imageEl.innerHTML = `<img src="${fighter.photo_url}" alt="${fighter.name}" style="width:100%; height:100%; object-fit:cover;">`;
    } else {
        imageEl.textContent = "🥊";
    }

    // Set name and nickname
    nameEl.textContent = fighter.name;
    if (fighter.nickname) {
        nicknameEl.textContent = `"${fighter.nickname}"`;
    } else {
        nicknameEl.remove();
    }

    // Set meta badges
    const orgBadge = `<span class="meta-badge">${
        fighter.last_organization_fight || fighter.organization || "N/A"
    }</span>`;
    const isFemale =
        fighter.gender === "female" ||
        (fighter.actual_weight_class || "").toLowerCase().includes("women") ||
        (fighter.weight_class || "").toLowerCase().includes("women");
    const genderBadge = `<span class="meta-badge">${
        isFemale ? "👩 Feminino" : "👨 Masculino"
    }</span>`;
    const weightClass =
        typeof translateWeightClass !== "undefined"
            ? translateWeightClass(
                  fighter.actual_weight_class || fighter.weight_class
              )
            : fighter.actual_weight_class || fighter.weight_class || "N/A";
    const weightBadge = `<span class="meta-badge">${weightClass}</span>`;
    metaEl.innerHTML = orgBadge + genderBadge + weightBadge;

    // Set stats
    const overall = Math.round(getOverall(fighter));
    card.querySelector(
        ".overall-value"
    ).innerHTML = `<strong>${overall}</strong>`;
    card.querySelector(".overall-stat .stat-fill").style.width = `${overall}%`;

    card.querySelector(".striking-value").textContent = fighter.striking;
    card.querySelector(
        ".striking-stat .stat-fill"
    ).style.width = `${fighter.striking}%`;

    card.querySelector(".grappling-value").textContent = fighter.grappling;
    card.querySelector(
        ".grappling-stat .stat-fill"
    ).style.width = `${fighter.grappling}%`;

    return card;
}

// Display fighters in grid
function displayFighters(fighters) {
    const container = document.getElementById("fightersList");

    if (!fighters || fighters.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>🥊 Nenhum lutador encontrado</p>
                <p class="text-muted">Tente ajustar os filtros</p>
            </div>
        `;
        return;
    }

    // Clear container
    container.innerHTML = "";

    // Use template for each fighter
    fighters.forEach((fighter) => {
        const card = createFighterCard(fighter);
        container.appendChild(card);
    });
}

// Search fighters
function searchFighters() {
    const name = document.getElementById("searchName").value;
    const organization = document.getElementById("filterOrg").value;
    const gender = document.getElementById("filterGender").value;
    const weight_class = document.getElementById("filterWeight").value;

    const filters = {};
    if (name) filters.name = name;
    if (organization) filters.last_organization_fight = organization;
    if (gender) filters.gender = gender;
    if (weight_class) filters.actual_weight_class = weight_class;

    AppState.currentFilters = filters;
    loadFighters(filters);
}

// Show create fighter modal
function showCreateFighter() {
    if (!requireAuth()) return;

    document.getElementById("createFighterModal").classList.add("active");
}

// Close create fighter modal
function closeCreateFighter() {
    document.getElementById("createFighterModal").classList.remove("active");
    document.getElementById("createFighterForm").reset();
}

// Update attribute value display
function updateValue(attr) {
    const value = document.getElementById(attr).value;
    document.getElementById(attr + "Value").textContent = value;
}

// Handle create fighter
async function handleCreateFighter(event) {
    event.preventDefault();

    if (!requireAuth()) return;

    const data = {
        name: document.getElementById("fighterName").value,
        nickname: document.getElementById("fighterNickname").value || null,
        last_organization_fight: document.getElementById("fighterOrg").value,
        gender: document.getElementById("fighterGender").value,
        actual_weight_class: document.getElementById("fighterWeight").value,
        fighting_style:
            document.getElementById("fighterStyle").value ||
            "Mixed Martial Arts",
        striking: parseInt(document.getElementById("striking").value),
        grappling: parseInt(document.getElementById("grappling").value),
        defense: parseInt(document.getElementById("defense").value),
        stamina: parseInt(document.getElementById("stamina").value),
        speed: parseInt(document.getElementById("speed").value),
        strategy: parseInt(document.getElementById("strategy").value),
    };

    try {
        showLoading("Criando lutador...");

        await api.createFighter(data);

        showToast("Lutador criado com sucesso!", "success");
        closeCreateFighter();
        loadFighters(AppState.currentFilters);
    } catch (error) {
        showToast(error.message || "Erro ao criar lutador", "error");
    } finally {
        hideLoading();
    }
}

// Show fighter details
async function showFighterDetails(id) {
    try {
        const modal = document.getElementById("fighterDetailsModal");
        const content = document.getElementById("fighterDetailsContent");

        // Show modal with loading
        modal.classList.add("active");
        content.innerHTML = '<div class="loading">Carregando detalhes...</div>';

        // Fetch fighter data
        const fighter = await api.getFighter(id);

        // Build details HTML
        content.innerHTML = `
            <div class="fighter-details-header">
                <div class="fighter-details-image">
                    ${
                        fighter.photo_url
                            ? `<img src="${fighter.photo_url}" alt="${fighter.name}">`
                            : "🥊"
                    }
                </div>
                <div class="fighter-details-info">
                    <div class="fighter-name-row">
                        <div>
                            <h2 class="fighter-details-name">${
                                fighter.name
                            }</h2>
                            ${
                                fighter.nickname
                                    ? `<p class="fighter-details-nickname">"${fighter.nickname}"</p>`
                                    : ""
                            }
                        </div>
                        <button class="btn-edit-fighter" onclick="openEditFighterModal('${
                            fighter.id
                        }')">
                            ✏️ Editar
                        </button>
                    </div>

                    <div class="fighter-details-badges">
                        <span class="detail-badge overall">Overall: ${Math.round(
                            getOverall(fighter)
                        )}</span>
                        ${
                            fighter.age
                                ? `<span class="detail-badge">👤 ${fighter.age} anos</span>`
                                : ""
                        }
                        <span class="detail-badge">
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
                        </span>
                        <span class="detail-badge">
                            ${
                                fighter.stance
                                    ? typeof translateStance !== "undefined"
                                        ? translateStance(fighter.stance)
                                        : fighter.stance
                                    : "N/A"
                            }
                        </span>
                        <span class="detail-badge">
                            ${
                                fighter.last_organization_fight ||
                                fighter.organization ||
                                "UFC"
                            }
                        </span>
                        ${
                            fighter.belt
                                ? `<span class="detail-badge">🏆 ${fighter.belt}</span>`
                                : ""
                        }
                    </div>

                    <div class="fighter-details-record">
                        Record: ${
                            typeof formatRecord !== "undefined"
                                ? formatRecord(fighter)
                                : fighter.record || "N/A"
                        }
                        ${
                            fighter.finish_rate
                                ? ` | Taxa de Finalização: ${Math.round(
                                      fighter.finish_rate
                                  )}%`
                                : ""
                        }
                    </div>
                </div>
            </div>

            <div class="fighter-details-body">
                <div>
                    <div class="fighter-details-section">
                        <h3>📊 Informações Físicas</h3>
                        <div class="physical-stats">
                            ${
                                fighter.height
                                    ? `
                                <div class="physical-stat-item">
                                    <div class="physical-stat-label">Altura</div>
                                    <div class="physical-stat-value">${
                                        typeof formatHeight !== "undefined"
                                            ? formatHeight(fighter.height)
                                            : fighter.height + " cm"
                                    }</div>
                                </div>
                            `
                                    : ""
                            }
                            ${
                                fighter.weight
                                    ? `
                                <div class="physical-stat-item">
                                    <div class="physical-stat-label">Peso</div>
                                    <div class="physical-stat-value">${
                                        typeof formatWeight !== "undefined"
                                            ? formatWeight(fighter.weight)
                                            : fighter.weight + " kg"
                                    }</div>
                                </div>
                            `
                                    : ""
                            }
                            ${
                                fighter.reach
                                    ? `
                                <div class="physical-stat-item">
                                    <div class="physical-stat-label">Alcance</div>
                                    <div class="physical-stat-value">${fighter.reach} cm</div>
                                </div>
                            `
                                    : ""
                            }
                            ${
                                fighter.stance
                                    ? `
                                <div class="physical-stat-item">
                                    <div class="physical-stat-label">Guarda</div>
                                    <div class="physical-stat-value">${
                                        typeof translateStance !== "undefined"
                                            ? translateStance(fighter.stance)
                                            : fighter.stance
                                    }</div>
                                </div>
                            `
                                    : ""
                            }
                            ${
                                fighter.fighting_style
                                    ? `
                                <div class="physical-stat-item">
                                    <div class="physical-stat-label">Estilo</div>
                                    <div class="physical-stat-value">${
                                        typeof translateFightingStyle !==
                                        "undefined"
                                            ? translateFightingStyle(
                                                  fighter.fighting_style
                                              )
                                            : fighter.fighting_style
                                    }</div>
                                </div>
                            `
                                    : ""
                            }
                        </div>
                    </div>

                    <div class="fighter-details-section">
                        <h3>⚡ Atributos de Luta</h3>
                        <div class="attributes-list">
                            <div class="attribute-item">
                                <span class="attribute-label">Striking</span>
                                <div class="attribute-bar-container">
                                    <div class="attribute-bar">
                                        <div class="attribute-bar-fill" style="width: ${
                                            fighter.striking
                                        }%"></div>
                                    </div>
                                </div>
                                <span class="attribute-value">${
                                    fighter.striking
                                }</span>
                            </div>
                            <div class="attribute-item">
                                <span class="attribute-label">Grappling</span>
                                <div class="attribute-bar-container">
                                    <div class="attribute-bar">
                                        <div class="attribute-bar-fill" style="width: ${
                                            fighter.grappling
                                        }%"></div>
                                    </div>
                                </div>
                                <span class="attribute-value">${
                                    fighter.grappling
                                }</span>
                            </div>
                            <div class="attribute-item">
                                <span class="attribute-label">Defense</span>
                                <div class="attribute-bar-container">
                                    <div class="attribute-bar">
                                        <div class="attribute-bar-fill" style="width: ${
                                            fighter.defense
                                        }%"></div>
                                    </div>
                                </div>
                                <span class="attribute-value">${
                                    fighter.defense
                                }</span>
                            </div>
                            <div class="attribute-item">
                                <span class="attribute-label">Stamina</span>
                                <div class="attribute-bar-container">
                                    <div class="attribute-bar">
                                        <div class="attribute-bar-fill" style="width: ${
                                            fighter.stamina
                                        }%"></div>
                                    </div>
                                </div>
                                <span class="attribute-value">${
                                    fighter.stamina
                                }</span>
                            </div>
                            <div class="attribute-item">
                                <span class="attribute-label">Speed</span>
                                <div class="attribute-bar-container">
                                    <div class="attribute-bar">
                                        <div class="attribute-bar-fill" style="width: ${
                                            fighter.speed
                                        }%"></div>
                                    </div>
                                </div>
                                <span class="attribute-value">${
                                    fighter.speed
                                }</span>
                            </div>
                            <div class="attribute-item">
                                <span class="attribute-label">Strategy</span>
                                <div class="attribute-bar-container">
                                    <div class="attribute-bar">
                                        <div class="attribute-bar-fill" style="width: ${
                                            fighter.strategy
                                        }%"></div>
                                    </div>
                                </div>
                                <span class="attribute-value">${
                                    fighter.strategy
                                }</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div>
                    <div class="fighter-details-section">
                        <h3>🥊 Cartel de Lutas</h3>
                        <div class="cartel-list">
                            ${
                                fighter.cartel && fighter.cartel.length > 0
                                    ? fighter.cartel
                                          .map((fight) => {
                                              // Normaliza o resultado (pode vir como "W", "L", "D" ou maiúsculo)
                                              const result = (
                                                  fight.result || ""
                                              )
                                                  .toUpperCase()
                                                  .trim();
                                              const resultClass =
                                                  result.toLowerCase();

                                              // Determina o label
                                              let resultLabel = "";
                                              if (result === "W") {
                                                  resultLabel = "VITÓRIA";
                                              } else if (result === "L") {
                                                  resultLabel = "DERROTA";
                                              } else if (
                                                  result === "D" ||
                                                  result === "DRAW"
                                              ) {
                                                  resultLabel = "EMPATE";
                                              } else if (
                                                  result === "NC" ||
                                                  result === "N/A"
                                              ) {
                                                  resultLabel = "SEM RESULTADO";
                                              }

                                              return `
                                    <div class="cartel-item ${resultClass}">
                                        <div class="cartel-header">
                                            ${
                                                resultLabel
                                                    ? `<span class="cartel-result ${resultClass}">${resultLabel}</span>`
                                                    : '<span class="cartel-result-unknown">LUTA</span>'
                                            }
                                            ${
                                                fight.date
                                                    ? `<span class="cartel-date">${fight.date}</span>`
                                                    : ""
                                            }
                                        </div>
                                        <div class="cartel-opponent">vs ${
                                            fight.opponent ||
                                            "Oponente desconhecido"
                                        }</div>
                                        <div class="cartel-details">
                                            ${
                                                fight.method
                                                    ? `${
                                                          typeof translateResultType !==
                                                          "undefined"
                                                              ? translateResultType(
                                                                    fight.method
                                                                )
                                                              : fight.method
                                                      }`
                                                    : ""
                                            }
                                            ${
                                                fight.round
                                                    ? ` • Round ${fight.round}`
                                                    : ""
                                            }
                                            ${
                                                fight.time
                                                    ? ` • ${fight.time}`
                                                    : ""
                                            }
                                            ${
                                                fight.event
                                                    ? `<br>${fight.event}`
                                                    : ""
                                            }
                                        </div>
                                    </div>
                                `;
                                          })
                                          .join("")
                                    : '<p style="color: var(--text-light); text-align: center; padding: 2rem;">Histórico de lutas não disponível</p>'
                            }
                        </div>
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        console.error("Error loading fighter details:", error);
        showToast("Erro ao carregar detalhes do lutador", "error");
        closeFighterDetails();
    }
}

// Close fighter details modal
function closeFighterDetails() {
    document.getElementById("fighterDetailsModal").classList.remove("active");
}

// Load fighter preview
async function loadFighterPreview(fighterId, containerId) {
    const container = document.getElementById(containerId);

    if (!fighterId) {
        container.innerHTML = "";
        return;
    }

    try {
        const fighter = await api.getFighter(fighterId);

        container.innerHTML = `
            <div class="fighter-preview-card">
                <h4>${fighter.name}</h4>
                ${
                    fighter.nickname
                        ? `<p style="font-style:italic; color:#666;">"${fighter.nickname}"</p>`
                        : ""
                }
                <div style="margin-top: 1rem;">
                    <div class="stat-bar">
                        <div class="stat-label">
                            <span>Overall</span>
                            <span><strong>${Math.round(
                                getOverall(fighter)
                            )}</strong></span>
                        </div>
                        <div class="stat-progress">
                            <div class="stat-fill" style="width: ${getOverall(
                                fighter
                            )}%"></div>
                        </div>
                    </div>
                    <div class="stat-bar">
                        <div class="stat-label"><span>Striking</span><span>${
                            fighter.striking
                        }</span></div>
                        <div class="stat-progress"><div class="stat-fill" style="width: ${
                            fighter.striking
                        }%"></div></div>
                    </div>
                    <div class="stat-bar">
                        <div class="stat-label"><span>Grappling</span><span>${
                            fighter.grappling
                        }</span></div>
                        <div class="stat-progress"><div class="stat-fill" style="width: ${
                            fighter.grappling
                        }%"></div></div>
                    </div>
                    <div class="stat-bar">
                        <div class="stat-label"><span>Defense</span><span>${
                            fighter.defense
                        }</span></div>
                        <div class="stat-progress"><div class="stat-fill" style="width: ${
                            fighter.defense
                        }%"></div></div>
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        console.error("Error loading fighter preview:", error);
    }
}

// Format weight class - DEPRECATED: Use translateWeightClass from utils.js instead
function formatWeightClass(weightClass) {
    // Use translateWeightClass if available, otherwise fallback to basic map
    if (typeof translateWeightClass !== "undefined") {
        return translateWeightClass(weightClass);
    }

    const map = {
        flyweight: "Peso-Mosca",
        bantamweight: "Peso-Galo",
        featherweight: "Peso-Pena",
        lightweight: "Peso-Leve",
        welterweight: "Peso-Meio-Médio",
        middleweight: "Peso-Médio",
        light_heavyweight: "Peso-Meio-Pesado",
        heavyweight: "Peso-Pesado",
    };
    return map[weightClass] || weightClass;
}

// Setup event listeners para fighters
let fightersListenersInitialized = false;

function setupFightersListeners() {
    // Evita adicionar listeners múltiplas vezes
    if (fightersListenersInitialized) {
        return;
    }

    // Event delegation for fighter cards
    const fightersList = document.getElementById("fightersList");
    if (fightersList) {
        fightersList.addEventListener("click", (e) => {
            const fighterCard = e.target.closest(".fighter-card");
            if (fighterCard) {
                const fighterId = fighterCard.dataset.fighterId;
                if (fighterId) {
                    showFighterDetails(fighterId);
                }
            }
        });
    }

    // Create fighter button
    const createFighterBtn = document.getElementById("createFighterBtn");
    if (createFighterBtn) {
        createFighterBtn.addEventListener("click", showCreateFighter);
    }

    // Create fighter form
    const createFighterForm = document.getElementById("createFighterForm");
    if (createFighterForm) {
        createFighterForm.addEventListener("submit", handleCreateFighter);
    }

    // Close modal button
    const closeModalBtns = document.querySelectorAll(
        "#createFighterModal .close, #fighterDetailsModal .close"
    );
    closeModalBtns.forEach((btn) => {
        btn.addEventListener("click", () => {
            closeCreateFighter();
            closeFighterDetails();
        });
    });

    // Search filters
    const searchName = document.getElementById("searchName");
    if (searchName) {
        searchName.addEventListener("keyup", searchFighters);
    }

    const filterOrg = document.getElementById("filterOrg");
    if (filterOrg) {
        filterOrg.addEventListener("change", searchFighters);
    }

    const filterGender = document.getElementById("filterGender");
    if (filterGender) {
        filterGender.addEventListener("change", searchFighters);
    }

    const filterWeight = document.getElementById("filterWeight");
    if (filterWeight) {
        filterWeight.addEventListener("change", searchFighters);
    }

    // Attribute sliders
    const attributeSliders = [
        "striking",
        "grappling",
        "defense",
        "stamina",
        "speed",
        "strategy",
    ];
    attributeSliders.forEach((attr) => {
        const slider = document.getElementById(attr);
        if (slider) {
            slider.addEventListener("input", () => updateValue(attr));
        }
    });

    fightersListenersInitialized = true;
}

// Open edit fighter modal
async function openEditFighterModal(fighterId) {
    try {
        // Get fighter data
        const fighter = await api.getFighter(fighterId);

        // Close details modal
        closeFighterDetails();

        // Populate edit form
        document.getElementById("editFighterId").value = fighter.id;
        document.getElementById("editFighterName").value = fighter.name;
        document.getElementById("editFighterNickname").value =
            fighter.nickname || "";
        document.getElementById("editFighterHeight").value =
            fighter.height_cm || "";
        document.getElementById("editFighterWeight").value =
            fighter.weight_lbs || "";
        document.getElementById("editFighterReach").value =
            fighter.reach_cm || "";
        document.getElementById("editFighterStance").value =
            fighter.stance || "";

        // Set attribute sliders
        document.getElementById("editStriking").value = fighter.striking || 50;
        document.getElementById("editGrappling").value =
            fighter.grappling || 50;
        document.getElementById("editDefense").value = fighter.defense || 50;
        document.getElementById("editStamina").value = fighter.stamina || 50;
        document.getElementById("editSpeed").value = fighter.speed || 50;
        document.getElementById("editStrategy").value = fighter.strategy || 50;

        // Update slider value displays
        updateEditSliderValue("striking", fighter.striking || 50);
        updateEditSliderValue("grappling", fighter.grappling || 50);
        updateEditSliderValue("defense", fighter.defense || 50);
        updateEditSliderValue("stamina", fighter.stamina || 50);
        updateEditSliderValue("speed", fighter.speed || 50);
        updateEditSliderValue("strategy", fighter.strategy || 50);

        // Show edit modal
        document.getElementById("editFighterModal").classList.add("active");
    } catch (error) {
        console.error("Error loading fighter for edit:", error);
        showToast("Erro ao carregar dados do lutador", "error");
    }
}

// Close edit fighter modal
function closeEditFighterModal() {
    document.getElementById("editFighterModal").classList.remove("active");
}

// Update slider value display in edit modal
function updateEditSliderValue(attr, value) {
    const display = document.getElementById(
        `edit${attr.charAt(0).toUpperCase() + attr.slice(1)}Value`
    );
    if (display) {
        display.textContent = value;
    }
}

// Save fighter edits
async function saveFighterEdits() {
    try {
        const fighterId = document.getElementById("editFighterId").value;

        const updates = {
            height_cm:
                parseFloat(
                    document.getElementById("editFighterHeight").value
                ) || null,
            weight_lbs:
                parseFloat(
                    document.getElementById("editFighterWeight").value
                ) || null,
            reach_cm:
                parseFloat(document.getElementById("editFighterReach").value) ||
                null,
            stance: document.getElementById("editFighterStance").value || null,
            striking: parseInt(document.getElementById("editStriking").value),
            grappling: parseInt(document.getElementById("editGrappling").value),
            defense: parseInt(document.getElementById("editDefense").value),
            stamina: parseInt(document.getElementById("editStamina").value),
            speed: parseInt(document.getElementById("editSpeed").value),
            strategy: parseInt(document.getElementById("editStrategy").value),
        };

        await api.updateFighter(fighterId, updates);
        showToast("Lutador atualizado com sucesso!", "success");
        closeEditFighterModal();

        // Reload fighter details
        showFighterDetails(fighterId);
    } catch (error) {
        console.error("Error updating fighter:", error);
        showToast("Erro ao atualizar lutador", "error");
    }
}
