// Main App Module

// Initialize app
document.addEventListener("DOMContentLoaded", async () => {
    console.log("🥊 FightBase App initialized");

    // Initialize theme
    initTheme();

    // Setup all event listeners
    setupEventListeners();

    // Check authentication
    await checkAuth();

    // Initialize sections based on hash
    const hash = window.location.hash.slice(1) || "home";
    showSection(hash);
});

// Theme Management
function initTheme() {
    // Check localStorage for saved theme
    const savedTheme = localStorage.getItem("theme") || "light";
    setTheme(savedTheme);

    // Setup theme toggle button
    const themeToggle = document.getElementById("themeToggle");
    if (themeToggle) {
        themeToggle.addEventListener("click", toggleTheme);
    }
}

function setTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);

    // Update icon
    const themeIcon = document.querySelector(".theme-icon");
    if (themeIcon) {
        themeIcon.textContent = theme === "dark" ? "☀️" : "🌙";
    }
}

function toggleTheme() {
    const currentTheme =
        document.documentElement.getAttribute("data-theme") || "light";
    const newTheme = currentTheme === "dark" ? "light" : "dark";
    setTheme(newTheme);

    // Toast notification
    showToast(
        `Tema ${newTheme === "dark" ? "escuro" : "claro"} ativado`,
        "success"
    );
}

// Show section
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll(".section").forEach((section) => {
        section.classList.remove("active");
    });

    // Show requested section
    const section = document.getElementById(sectionName + "Section");
    if (section) {
        section.classList.add("active");
    }

    // Update nav links
    document.querySelectorAll(".nav-link").forEach((link) => {
        link.classList.remove("active");
    });
    const activeLink = document.querySelector(
        `.nav-link[href="#${sectionName}"]`
    );
    if (activeLink) {
        activeLink.classList.add("active");
    }

    // Update URL hash
    window.location.hash = sectionName;

    // Load section data
    switch (sectionName) {
        case "fighters":
            loadFighters();
            break;
        case "simulate":
            setupFighterSearch();
            loadRecentSimulations();
            break;
        case "events":
            initEventsSection();
            break;
        case "createEvent":
            // Apenas mostra o formulário
            break;
        case "rankings":
            loadRankings();
            break;
        case "home":
            loadHomeStats();
            break;
    }

    // Scroll to top
    window.scrollTo({ top: 0, behavior: "smooth" });
}

// Load home statistics
async function loadHomeStats() {
    try {
        const stats = await api.getFighterStats();

        if (stats && stats.total_fighters) {
            document.getElementById("totalFighters").textContent =
                stats.total_fighters;
        }

        // Try to load simulation count
        try {
            const simStats = await api.getSimulationStats();
            if (simStats && simStats.total_simulations !== undefined) {
                document.getElementById("totalSimulations").textContent =
                    simStats.total_simulations.toLocaleString("pt-BR");
            }
        } catch (e) {
            // Simulation endpoint might require auth
            console.log("Could not load simulations count");
        }
    } catch (error) {
        console.error("Error loading stats:", error);
    }
}

// Setup all event listeners
function setupEventListeners() {
    // Navigation links
    const navLinks = document.querySelectorAll(".nav-link");
    navLinks.forEach((link) => {
        link.addEventListener("click", (e) => {
            e.preventDefault();
            const href = link.getAttribute("href");
            if (href && href.startsWith("#")) {
                showSection(href.substring(1));
            }
        });
    });

    // Hero action buttons
    const heroFightersBtn = document.querySelector(
        ".hero-actions .btn-primary"
    );
    if (heroFightersBtn) {
        heroFightersBtn.addEventListener("click", () =>
            showSection("fighters")
        );
    }

    const heroSimulateBtn = document.querySelector(
        ".hero-actions .btn-secondary"
    );
    if (heroSimulateBtn) {
        heroSimulateBtn.addEventListener("click", () =>
            showSection("simulate")
        );
    }

    // Auth buttons in nav
    const loginNavBtn = document.getElementById("loginBtn");
    if (loginNavBtn) {
        loginNavBtn.addEventListener("click", () => showSection("login"));
    }

    const registerNavBtn = document.getElementById("registerBtn");
    if (registerNavBtn) {
        registerNavBtn.addEventListener("click", () => showSection("register"));
    }

    const logoutBtn = document.querySelector("#userMenu button");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", logout);
    }

    // Register page link
    const registerLinks = document.querySelectorAll(
        'a[href="#"][onclick*="register"]'
    );
    registerLinks.forEach((link) => {
        link.removeAttribute("onclick");
        link.addEventListener("click", (e) => {
            e.preventDefault();
            showSection("register");
        });
    });

    // Login page link
    const loginLinks = document.querySelectorAll(
        'a[href="#"][onclick*="login"]'
    );
    loginLinks.forEach((link) => {
        link.removeAttribute("onclick");
        link.addEventListener("click", (e) => {
            e.preventDefault();
            showSection("login");
        });
    });

    // Events section buttons
    const createNewEventBtn = document.getElementById("createNewEventBtn");
    if (createNewEventBtn) {
        createNewEventBtn.addEventListener("click", () =>
            showSection("createEvent")
        );
    }

    const backToEventsBtn = document.getElementById("backToEventsBtn");
    if (backToEventsBtn) {
        backToEventsBtn.addEventListener("click", () => {
            if (typeof resetEventForm === "function") resetEventForm();
            showSection("events");
        });
    }

    // Cancel event button
    const cancelEventBtn = document.getElementById("cancelEventBtn");
    if (cancelEventBtn) {
        cancelEventBtn.addEventListener("click", () => {
            if (typeof resetEventForm === "function") resetEventForm();
            showSection("events");
        });
    }

    // Setup module event listeners
    if (typeof setupFightersListeners === "function") {
        setupFightersListeners();
    }

    if (typeof setupSimulationListeners === "function") {
        setupSimulationListeners();
    }

    if (typeof setupRankingsListeners === "function") {
        setupRankingsListeners();
    }

    if (typeof setupEventsListeners === "function") {
        setupEventsListeners();
    }

    const rankingWeight = document.getElementById("rankingWeight");
    if (rankingWeight) {
        rankingWeight.addEventListener("change", loadRankings);
    }

    // Simulate button
    const simulateBtn = document.getElementById("simulateBtn");
    if (simulateBtn) {
        simulateBtn.removeAttribute("onclick");
        simulateBtn.addEventListener("click", runSimulation);
    }

    // Close modal on outside click
    window.addEventListener("click", (event) => {
        if (event.target.classList.contains("modal")) {
            event.target.classList.remove("active");
        }
    });

    // Setup module-specific listeners
    if (typeof setupAuthListeners === "function") {
        setupAuthListeners();
    }

    if (typeof setupFightersListeners === "function") {
        setupFightersListeners();
    }

    if (typeof setupEventsListeners === "function") {
        setupEventsListeners();
    }
}

// Handle browser back/forward
window.addEventListener("hashchange", () => {
    const hash = window.location.hash.slice(1) || "home";
    showSection(hash);
});

// Error handling
window.addEventListener("error", (event) => {
    console.error("Global error:", event.error);
});

window.addEventListener("unhandledrejection", (event) => {
    console.error("Unhandled promise rejection:", event.reason);
});

console.log(`
    🥊 FightBase Frontend
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    API: ${API_BASE_URL}
    Status: Ready

    Features:
    ✓ Authentication (Register/Login)
    ✓ Fighter Management (CRUD)
    ✓ Fight Simulation
    ✓ Rankings
    ✓ Recent Simulations

    Nota: Sistema usa Firebase Auth.
    Para funcionalidade completa, configure
    Firebase Client SDK em produção.
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
`);
