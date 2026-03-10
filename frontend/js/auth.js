// Authentication Module

// Check if user is logged in on page load
async function checkAuth() {
    const token = localStorage.getItem("idToken");

    // Check URL for Google SSO redirect token
    const urlParams = new URLSearchParams(window.location.search);
    const tokenFromUrl = urlParams.get("token");

    if (tokenFromUrl) {
        localStorage.setItem("idToken", tokenFromUrl);
        // Clean up the URL
        window.history.replaceState({}, document.title, window.location.pathname);
        api.setToken(tokenFromUrl);
        const user = await api.getCurrentUser();
        if (user) {
            AppState.setCurrentUser(user);
            updateAuthUI(true);
            showToast("Login via Google realizado com sucesso! 🥊", "success");
            return true;
        }
    }

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

// 🎲 Gamification Logic

// Password Humor Meter
function updatePasswordMeter(password) {
    const meterFill = document.getElementById("meterFill");
    const meterText = document.getElementById("meterText");

    // Simple strength calculation
    let strength = 0;
    if (password.length > 5) strength += 20;
    if (password.length > 8) strength += 20;
    if (/[A-Z]/.test(password)) strength += 20;
    if (/[0-9]/.test(password)) strength += 20;
    if (/[^A-Za-z0-9]/.test(password)) strength += 20;

    // Humor texts
    let color = "var(--error)";
    let text = "Senha de avó 👵";

    if (strength >= 40) {
        color = "var(--warning)";
        text = "Tá melhorando... 😐";
    }
    if (strength >= 80) {
        color = "var(--success)";
        text = "Nível Hacker 🐱‍💻";
    }
    if (strength === 100) {
        color = "#00F0FF";
        text = "NASA, é você? 🚀";
    }

    if (password.length === 0) {
        strength = 0;
        text = "Digite sua senha...";
        color = "transparent";
    }

    meterFill.style.width = `${strength}%`;
    meterFill.style.backgroundColor = color;
    meterText.textContent = text;
    meterText.style.color = color;
}

// Age Validation (13+)
function validateAge(dateString) {
    const birthday = new Date(dateString);
    const today = new Date();
    let age = today.getFullYear() - birthday.getFullYear();
    const m = today.getMonth() - birthday.getMonth();

    if (m < 0 || (m === 0 && today.getDate() < birthday.getDate())) {
        age--;
    }

    return age >= 13;
}

// 🎉 Confetti Celebration
function triggerCelebration() {
    const duration = 3000;
    const end = Date.now() + duration;

    (function frame() {
        // launch a few confetti from the left edge
        confetti({
            particleCount: 7,
            angle: 60,
            spread: 55,
            origin: { x: 0 },
            colors: ['#FF2E4D', '#00F0FF', '#ffffff']
        });
        // and launch a few from the right edge
        confetti({
            particleCount: 7,
            angle: 120,
            spread: 55,
            origin: { x: 1 },
            colors: ['#FF2E4D', '#00F0FF', '#ffffff']
        });

        if (Date.now() < end) {
            requestAnimationFrame(frame);
        }
    }());
}

// Register
async function handleRegister(event) {
    event.preventDefault();

    const name = document.getElementById("registerName").value;
    const email = document.getElementById("registerEmail").value;
    const password = document.getElementById("registerPassword").value;

    // New Fields
    const username = document.getElementById("registerUsername").value;
    const birthday = document.getElementById("registerBirthday").value;
    const avatar = document.getElementById("selectedAvatar").value;

    // Validate Age
    if (!validateAge(birthday)) {
        showToast("Você precisa ter pelo menos 13 anos para participar do Fight Club! 👶", "error");
        return;
    }

    try {
        showLoading("Criando conta...");

        // Mock API call to include new fields (backend upgrade needed later)
        // For now, we register with standard fields
        await api.register({
            name,
            email,
            password,
            // Assuming API will ignore extra fields for now or we store them in User profile later
            username,
            birthday,
            avatar
        });

        // 🎉 SUCCESS!
        triggerCelebration();

        showToast("Conta criada com sucesso! Bem-vindo ao octógono! 🥊", "success");

        // Wait for confetti before switching
        setTimeout(() => {
            showSection("login");
            // Pre-fill login
            document.getElementById("loginEmail").value = email;
            document.getElementById("registerForm").reset();
        }, 1500);

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

// Google Login
async function handleGoogleLogin() {
    showToast("Redirecionando para o Google...", "info");
    // Redireciona para o backend
    window.location.href = `${API_BASE_URL}/auth/google/login`;
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
let authListenersInitialized = false;

function setupAuthListeners() {
    // Evita adicionar listeners múltiplas vezes
    if (authListenersInitialized) {
        return;
    }

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

    // PasswordMeter Listener
    const registerPassword = document.getElementById("registerPassword");
    if (registerPassword) {
        registerPassword.addEventListener("input", (e) => updatePasswordMeter(e.target.value));
    }

    // Avatar Selection Logic
    const avatarOptions = document.querySelectorAll(".avatar-option");
    avatarOptions.forEach(opt => {
        opt.addEventListener("click", () => {
             // Remove select from all
             avatarOptions.forEach(o => o.classList.remove("selected"));
             // Add to clicked
             opt.classList.add("selected");
             // Update hidden input
             document.getElementById("selectedAvatar").value = opt.dataset.avatar;
        });
    });

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

    authListenersInitialized = true;
}
