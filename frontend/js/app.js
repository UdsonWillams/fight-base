// Main App Module

let loadingOverlay = null;

// Initialize app
document.addEventListener("DOMContentLoaded", async () => {
    console.log("🥊 FightBase App initialized");

    // Check authentication
    await checkAuth();

    // Load home stats
    loadHomeStats();

    // Initialize sections based on hash
    const hash = window.location.hash.slice(1) || "home";
    showSection(hash);
});

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
        `[onclick="showSection('${sectionName}')"]`
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
            const recentSims = await api.getRecentSimulations(100);
            if (recentSims) {
                document.getElementById("totalSimulations").textContent =
                    recentSims.length;
            }
        } catch (e) {
            // Simulation endpoint might require auth
            console.log("Could not load simulations count");
        }
    } catch (error) {
        console.error("Error loading stats:", error);
    }
}

// Show toast notification
function showToast(message, type = "success") {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.className = `toast ${type} show`;

    setTimeout(() => {
        toast.classList.remove("show");
    }, 3000);
}

// Show loading overlay
function showLoading(message = "Carregando...") {
    if (!loadingOverlay) {
        loadingOverlay = document.createElement("div");
        loadingOverlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            color: white;
            font-size: 1.5rem;
        `;
        document.body.appendChild(loadingOverlay);
    }

    loadingOverlay.innerHTML = `
        <div style="text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">⏳</div>
            <div>${message}</div>
        </div>
    `;
    loadingOverlay.style.display = "flex";
}

// Hide loading overlay
function hideLoading() {
    if (loadingOverlay) {
        loadingOverlay.style.display = "none";
    }
}

// Close modal on outside click
window.onclick = function (event) {
    const modal = document.getElementById("createFighterModal");
    if (event.target === modal) {
        closeCreateFighter();
    }
};

// Handle browser back/forward
window.addEventListener("hashchange", () => {
    const hash = window.location.hash.slice(1) || "home";
    showSection(hash);
});

// Utility: Format date
function formatDate(dateString) {
    if (!dateString) return "";

    const date = new Date(dateString);
    return date.toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}

// Utility: Capitalize
function capitalize(str) {
    if (!str) return "";
    return str.charAt(0).toUpperCase() + str.slice(1);
}

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
