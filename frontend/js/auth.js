// Authentication Module

// Check if user is logged in on page load
async function checkAuth() {
    const token = localStorage.getItem("idToken");

    if (token) {
        try {
            // Check if token is expired
            const payload = JSON.parse(atob(token.split(".")[1]));
            const exp = payload.exp * 1000; // Convert to milliseconds

            if (Date.now() >= exp) {
                console.log("Token expired");
                logout();
                return false;
            }

            api.setToken(token);
            const user = await api.getCurrentUser();

            if (user) {
                AppState.setCurrentUser(user);
                updateAuthUI(true);
                return true;
            } else {
                logout();
                return false;
            }
        } catch (error) {
            console.error("Auth check failed:", error);
            logout();
            return false;
        }
    }

    updateAuthUI(false);
    return false;
}

// Register
async function handleRegister(event) {
    event.preventDefault();

    const name = document.getElementById("registerName").value;
    const email = document.getElementById("registerEmail").value;
    const password = document.getElementById("registerPassword").value;

    try {
        showLoading("Criando conta...");

        await api.register({
            name,
            email,
            password,
        });

        showToast("Conta criada com sucesso! Faça login.", "success");
        showSection("login");

        // Pre-fill login form
        document.getElementById("loginEmail").value = email;

        // Clear register form
        document.getElementById("registerForm").reset();
    } catch (error) {
        showToast(error.message || "Erro ao criar conta", "error");
    } finally {
        hideLoading();
    }
}

// Login
async function handleLogin(event) {
    event.preventDefault();

    const email = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPassword").value;

    try {
        showLoading("Fazendo login...");

        const response = await api.login(email, password);

        // API retorna { access_token, token_type }
        api.setToken(response.access_token);

        // Get current user info
        const user = await api.getCurrentUser();
        AppState.setCurrentUser(user);

        showToast("Login realizado com sucesso!", "success");
        updateAuthUI(true);
        showSection("home");

        // Reload data
        loadHomeStats();
    } catch (error) {
        showToast(error.message || "Credenciais inválidas", "error");
    } finally {
        hideLoading();
    }
}

// Logout
function logout() {
    api.setToken(null);
    AppState.clearUser();
    updateAuthUI(false);
    showSection("home");
    showToast("Você saiu da sua conta", "success");
}

// Update UI based on auth state
function updateAuthUI(isLoggedIn) {
    const loginBtn = document.getElementById("loginBtn");
    const registerBtn = document.getElementById("registerBtn");
    const userMenu = document.getElementById("userMenu");
    const userName = document.getElementById("userName");
    const createFighterBtn = document.getElementById("createFighterBtn");

    const currentUser = AppState.getCurrentUser();

    if (isLoggedIn && currentUser) {
        loginBtn.style.display = "none";
        registerBtn.style.display = "none";
        userMenu.style.display = "flex";
        userName.textContent = currentUser.name;

        if (createFighterBtn) {
            createFighterBtn.style.display = "block";
        }
    } else {
        loginBtn.style.display = "block";
        registerBtn.style.display = "block";
        userMenu.style.display = "none";

        if (createFighterBtn) {
            createFighterBtn.style.display = "none";
        }
    }
}

// Google Login (Firebase integration - requires configuration)
async function handleGoogleLogin() {
    showToast(
        "Login com Google não configurado. Use email e senha.",
        "warning"
    );
    // TODO: Implementar integração com Firebase quando necessário
}

// Check if user is authenticated
function requireAuth() {
    const currentUser = AppState.getCurrentUser();
    if (!currentUser) {
        showToast("Você precisa estar logado", "error");
        showSection("login");
        return false;
    }
    return true;
}

// Toggle password visibility
function togglePasswordVisibility(inputId) {
    const input = document.getElementById(inputId);
    const button = input.parentElement.querySelector(".password-toggle");

    if (input.type === "password") {
        input.type = "text";
        button.textContent = "👁️‍🗨️"; // Olho fechado
    } else {
        input.type = "password";
        button.textContent = "👁️"; // Olho aberto
    }
}

// Setup event listeners para autenticação
function setupAuthListeners() {
    // Login form
    const loginForm = document.getElementById("loginForm");
    if (loginForm) {
        loginForm.addEventListener("submit", handleLogin);
    }

    // Register form
    const registerForm = document.getElementById("registerForm");
    if (registerForm) {
        registerForm.addEventListener("submit", handleRegister);
    }

    // Password toggles
    const passwordToggles = document.querySelectorAll(".password-toggle");
    passwordToggles.forEach((toggle) => {
        toggle.addEventListener("click", (e) => {
            const input = e.target
                .closest(".password-input-wrapper")
                .querySelector("input");
            togglePasswordVisibility(input.id);
        });
    });

    // Google login button
    const googleLoginBtn = document.querySelector(".btn-google");
    if (googleLoginBtn) {
        googleLoginBtn.addEventListener("click", handleGoogleLogin);
    }
}
