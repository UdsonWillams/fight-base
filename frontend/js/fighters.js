// Fighters Module

// Helper function to get overall rating
function getOverall(fighter) {
    return fighter.overall_rating || fighter.overall || 75;
}

// Load fighters list
async function loadFighters(filters = {}) {
    try {
        const params = {
            limit: 50,
            offset: 0,
            ...filters,
        };

        const response = await api.getFighters(params);
        AppState.allFighters = response.fighters || [];

        displayFighters(AppState.allFighters);
    } catch (error) {
        console.error("Error loading fighters:", error);
        showToast("Erro ao carregar lutadores", "error");
    }
}

// Display fighters in grid
function displayFighters(fighters) {
    const container = document.getElementById("fightersList");

    if (!fighters || fighters.length === 0) {
        container.innerHTML =
            '<div class="loading">Nenhum lutador encontrado</div>';
        return;
    }

    container.innerHTML = fighters
        .map(
            (fighter) => `
        <div class="fighter-card" onclick="showFighterDetails('${fighter.id}')">
            <div class="fighter-image">
                ${
                    fighter.photo_url
                        ? `<img src="${fighter.photo_url}" alt="${fighter.name}" style="width:100%; height:100%; object-fit:cover;">`
                        : "🥊"
                }
            </div>
            <div class="fighter-info">
                <div class="fighter-name">${fighter.name}</div>
                ${
                    fighter.nickname
                        ? `<div class="fighter-nickname">"${fighter.nickname}"</div>`
                        : ""
                }
                <div class="fighter-meta">
                    <span class="meta-badge">${
                        fighter.last_organization_fight ||
                        fighter.organization ||
                        "N/A"
                    }</span>
                    <span class="meta-badge">${
                        fighter.gender === "female"
                            ? "👩 Feminino"
                            : "👨 Masculino"
                    }</span>
                    <span class="meta-badge">${
                        typeof translateWeightClass !== "undefined"
                            ? translateWeightClass(
                                  fighter.actual_weight_class ||
                                      fighter.weight_class
                              )
                            : fighter.actual_weight_class ||
                              fighter.weight_class ||
                              "N/A"
                    }</span>
                </div>
                <div class="fighter-stats">
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
                        <div class="stat-label">
                            <span>Striking</span>
                            <span>${fighter.striking}</span>
                        </div>
                        <div class="stat-progress">
                            <div class="stat-fill" style="width: ${
                                fighter.striking
                            }%"></div>
                        </div>
                    </div>
                    <div class="stat-bar">
                        <div class="stat-label">
                            <span>Grappling</span>
                            <span>${fighter.grappling}</span>
                        </div>
                        <div class="stat-progress">
                            <div class="stat-fill" style="width: ${
                                fighter.grappling
                            }%"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
        )
        .join("");
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
                    <h2 class="fighter-details-name">${fighter.name}</h2>
                    ${
                        fighter.nickname
                            ? `<p class="fighter-details-nickname">"${fighter.nickname}"</p>`
                            : ""
                    }

                    <div class="fighter-details-badges">
                        <span class="detail-badge overall">Overall: ${Math.round(
                            getOverall(fighter)
                        )}</span>
                        <span class="detail-badge">${
                            typeof translateGender !== "undefined"
                                ? translateGender(fighter.gender)
                                : fighter.gender
                        }</span>
                        <span class="detail-badge">${
                            typeof translateWeightClass !== "undefined"
                                ? translateWeightClass(
                                      fighter.actual_weight_class ||
                                          fighter.weight_class
                                  )
                                : fighter.actual_weight_class ||
                                  fighter.weight_class ||
                                  "N/A"
                        }</span>
                        <span class="detail-badge">${
                            fighter.last_organization_fight ||
                            fighter.organization ||
                            "N/A"
                        }</span>
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
                                          .map(
                                              (fight) => `
                                    <div class="cartel-item ${
                                        fight.result
                                            ? fight.result.toLowerCase()
                                            : ""
                                    }">
                                        <div class="cartel-header">
                                            <span class="cartel-result ${
                                                fight.result
                                                    ? fight.result.toLowerCase()
                                                    : ""
                                            }">${fight.result || "N/A"}</span>
                                            <span>${
                                                fight.date ||
                                                "Data desconhecida"
                                            }</span>
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
                                `
                                          )
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

// Fighter Search for Simulation
function setupFighterSearch() {
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

    // Close search results when clicking outside
    document.addEventListener("click", (e) => {
        if (!e.target.closest(".fighter-search-container")) {
            document.getElementById("fighter1Results").classList.remove("show");
            document.getElementById("fighter2Results").classList.remove("show");
        }
    });
}

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
        <div class="search-result-item" onclick="selectFighter('${
            fighter.id
        }', ${fighterNum})">
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

function selectFighter(fighterId, fighterNum) {
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

    // Load fighter details and update input
    loadFighterForSelection(fighterId, fighterNum);

    // Hide results
    resultsContainer.classList.remove("show");
}

async function loadFighterForSelection(fighterId, fighterNum) {
    try {
        const fighter = await api.getFighter(fighterId);

        // Update search input with fighter name
        const searchInput =
            fighterNum === 1
                ? document.getElementById("fighter1Search")
                : document.getElementById("fighter2Search");
        searchInput.value = fighter.name;

        // Load preview
        const containerId =
            fighterNum === 1 ? "fighter1Preview" : "fighter2Preview";
        loadFighterPreview(fighterId, containerId);
    } catch (error) {
        console.error("Error loading fighter:", error);
        showToast("Erro ao carregar lutador", "error");
    }
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

// Format weight class
function formatWeightClass(weightClass) {
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
function setupFightersListeners() {
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
}
