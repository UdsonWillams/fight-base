// Authentication Module

let currentUser = null;

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
            currentUser = await api.getCurrentUser();

            if (currentUser) {
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
    let password = document.getElementById("registerPassword").value;

    // Bcrypt has a 72 byte limit, truncate if necessary
    const passwordBytes = new TextEncoder().encode(password);
    if (passwordBytes.length > 72) {
        showToast("Senha muito longa. Será truncada para 72 bytes.", "warning");
        // Decode back to string, truncating at 72 bytes
        password = new TextDecoder().decode(passwordBytes.slice(0, 72));
    }

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
    let password = document.getElementById("loginPassword").value;

    // Bcrypt has a 72 byte limit, truncate if necessary
    const passwordBytes = new TextEncoder().encode(password);
    if (passwordBytes.length > 72) {
        // Decode back to string, truncating at 72 bytes
        password = new TextDecoder().decode(passwordBytes.slice(0, 72));
    }

    try {
        showLoading("Fazendo login...");

        const response = await api.login(email, password);

        // API retorna { access_token, token_type }
        api.setToken(response.access_token);

        // Get current user info
        currentUser = await api.getCurrentUser();

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
    currentUser = null;
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
