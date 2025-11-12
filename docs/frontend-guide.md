# 🎨 FightBase - Guia do Frontend

> Documentação completa da interface web do FightBase

## 📁 Estrutura de Arquivos

```
frontend/
├── index.html              # Página principal
├── css/
│   └── styles.css          # Estilos com suporte a dark mode
└── js/
    ├── app.js              # Inicialização e tema
    ├── api.js              # Cliente da API
    ├── auth.js             # Autenticação
    ├── fighters.js         # Gestão de lutadores
    ├── events.js           # Gestão de eventos
    ├── simulations.js      # Simulações
    ├── rankings.js         # Rankings
    └── utils.js            # Utilitários (toast, loading, etc)
```

## 🎯 Principais Recursos

### ✨ UX Melhorias Implementadas

1. **Dark Mode Completo**

   - Toggle entre tema claro e escuro
   - Persistência com localStorage
   - CSS variables para cores
   - Transições suaves

2. **Auto-save de Formulários**

   - Salva automaticamente após 2 segundos
   - Expiração de 7 dias
   - Indicador visual de salvamento
   - Recuperação automática ao recarregar

3. **Busca com Debounce**

   - 300ms de delay
   - Busca em tempo real
   - Feedback visual

4. **Skeleton Loading**

   - Estados de carregamento elegantes
   - Para lutadores e eventos
   - Melhor percepção de performance

5. **Toast Notifications**
   - Ícones contextuais
   - Auto-dismiss
   - Tipos: success, error, info, warning

## 🎨 Sistema de Temas

### CSS Variables (Light Mode)

```css
:root {
  --bg: #f5f5f5;
  --card-bg: #ffffff;
  --text: #1a1a1a;
  --text-light: #4a4a4a;
  --text-muted: #8a8a8a;
  --primary: #ff4655;
  --secondary: #1a1a1a;
  --border: #e0e0e0;
  --shadow: rgba(0, 0, 0, 0.08);
}
```

### CSS Variables (Dark Mode)

```css
[data-theme="dark"] {
  --bg: #0d1117;
  --card-bg: #161b22;
  --text: #e6edf3;
  --text-light: #9198a1;
  --text-muted: #6e7681;
  --primary: #ff4655;
  --secondary: #58a6ff;
  --border: #30363d;
  --shadow: rgba(0, 0, 0, 0.4);
}
```

### Toggle de Tema

```javascript
// app.js
function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme");
  const newTheme = current === "dark" ? "light" : "dark";
  setTheme(newTheme);
  showToast(`Tema ${newTheme === "dark" ? "escuro" : "claro"} ativado`, "info");
}

function setTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("theme", theme);

  const icon = document.getElementById("themeIcon");
  if (icon) {
    icon.textContent = theme === "dark" ? "☀️" : "🌙";
  }
}
```

## 🔧 Módulos JavaScript

### API Client (api.js)

Cliente HTTP com autenticação automática:

```javascript
class APIClient {
  constructor(baseURL = "http://localhost:8000") {
    this.baseURL = baseURL;
  }

  async request(endpoint, options = {}) {
    const token = localStorage.getItem("access_token");

    const config = {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
    };

    const response = await fetch(`${this.baseURL}${endpoint}`, config);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Erro na requisição");
    }

    return response.json();
  }
}
```

### Autenticação (auth.js)

```javascript
async function login(email, password) {
  try {
    const data = await api.login(email, password);
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("user", JSON.stringify(data.user));
    showToast("Login realizado com sucesso!", "success");
    return true;
  } catch (error) {
    showToast(error.message, "error");
    return false;
  }
}

function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("user");
  showToast("Logout realizado", "info");
  showSection("home");
}

function isAuthenticated() {
  return !!localStorage.getItem("access_token");
}
```

### Fighters (fighters.js)

Gestão completa de lutadores:

```javascript
// Listar com busca e filtros
async function loadFighters(filters = {}) {
  showSkeleton("fightersGrid", "fighter");

  try {
    const fighters = await api.getFighters(filters);
    displayFighters(fighters);
  } catch (error) {
    showToast("Erro ao carregar lutadores", "error");
  }
}

// Busca com debounce
let searchTimeout;
function onSearchChange(query) {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    loadFighters({ search: query });
  }, 300);
}

// Criar lutador
async function createFighter(data) {
  try {
    const fighter = await api.createFighter(data);
    showToast("Lutador criado!", "success");
    loadFighters();
    closeModal();
  } catch (error) {
    showToast(error.message, "error");
  }
}
```

### Events (events.js)

Com auto-save:

```javascript
const AUTO_SAVE_DELAY = 2000;
const DRAFT_EXPIRY_DAYS = 7;

let autoSaveTimeout;

function setupAutoSave(formId) {
  const form = document.getElementById(formId);
  const inputs = form.querySelectorAll("input, textarea, select");

  inputs.forEach((input) => {
    input.addEventListener("input", () => {
      clearTimeout(autoSaveTimeout);
      showAutoSaveIndicator("Salvando...");

      autoSaveTimeout = setTimeout(() => {
        saveFormDraft(formId, getFormData(form));
        showAutoSaveIndicator("✓ Salvo");
      }, AUTO_SAVE_DELAY);
    });
  });
}

function saveFormDraft(formId, data) {
  const draft = {
    data,
    timestamp: Date.now(),
  };
  localStorage.setItem(`draft_${formId}`, JSON.stringify(draft));
}

function loadFormDraft(formId) {
  const saved = localStorage.getItem(`draft_${formId}`);
  if (!saved) return null;

  const draft = JSON.parse(saved);
  const age = Date.now() - draft.timestamp;
  const expiryMs = DRAFT_EXPIRY_DAYS * 24 * 60 * 60 * 1000;

  if (age > expiryMs) {
    localStorage.removeItem(`draft_${formId}`);
    return null;
  }

  return draft.data;
}
```

### Utils (utils.js)

Utilitários compartilhados:

```javascript
// Toast Notifications
function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;

  const icons = {
    success: "✓",
    error: "✗",
    warning: "⚠",
    info: "ℹ",
  };

  toast.innerHTML = `
        <span class="toast-icon">${icons[type]}</span>
        <span>${message}</span>
    `;

  document.body.appendChild(toast);

  setTimeout(() => toast.classList.add("show"), 100);
  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Loading Skeleton
function showSkeleton(containerId, type = "fighter") {
  const container = document.getElementById(containerId);
  const skeletonHTML =
    type === "fighter" ? getSkeletonFighter() : getSkeletonEvent();

  container.innerHTML = skeletonHTML.repeat(6);
}

function getSkeletonFighter() {
  return `
        <div class="skeleton-card">
            <div class="skeleton skeleton-title"></div>
            <div class="skeleton skeleton-text"></div>
            <div class="skeleton skeleton-text"></div>
            <div class="skeleton skeleton-button"></div>
        </div>
    `;
}

// Debounce
function debounce(func, delay) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), delay);
  };
}

// Format Date
function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString("pt-BR");
}

// Validate Form
function validateForm(formId) {
  const form = document.getElementById(formId);
  const inputs = form.querySelectorAll("[required]");

  for (const input of inputs) {
    if (!input.value.trim()) {
      showToast(`Campo "${input.placeholder}" é obrigatório`, "error");
      input.focus();
      return false;
    }
  }

  return true;
}
```

## 🎭 Componentes Reutilizáveis

### Modal

```javascript
function showModal(modalId) {
  const modal = document.getElementById(modalId);
  modal.classList.add("active");
  document.body.style.overflow = "hidden";
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  modal.classList.remove("active");
  document.body.style.overflow = "";
}

// Fechar com ESC
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    document.querySelectorAll(".modal.active").forEach(closeModal);
  }
});
```

### Cards Dinâmicos

```javascript
function createFighterCard(fighter) {
  return `
        <div class="fighter-card" data-id="${fighter.id}">
            <div class="fighter-header">
                <h3>${fighter.name}</h3>
                <span class="badge">${fighter.organization}</span>
            </div>
            <div class="fighter-info">
                <span>${fighter.weight_class}</span>
                <span>Overall: ${fighter.overall_rating}</span>
            </div>
            <div class="fighter-stats">
                <div class="stat">
                    <span>STR</span>
                    <strong>${fighter.striking}</strong>
                </div>
                <div class="stat">
                    <span>GRP</span>
                    <strong>${fighter.grappling}</strong>
                </div>
                <div class="stat">
                    <span>DEF</span>
                    <strong>${fighter.defense}</strong>
                </div>
            </div>
            <div class="fighter-actions">
                <button onclick="viewFighter('${fighter.id}')">Ver Detalhes</button>
                <button onclick="editFighter('${fighter.id}')">Editar</button>
            </div>
        </div>
    `;
}
```

## 📱 Responsividade

### Breakpoints

```css
/* Mobile */
@media (max-width: 768px) {
  .fighters-grid {
    grid-template-columns: 1fr;
  }

  .navbar {
    flex-direction: column;
  }

  .modal-content {
    width: 95%;
    margin: 20px;
  }
}

/* Tablet */
@media (min-width: 769px) and (max-width: 1024px) {
  .fighters-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Desktop */
@media (min-width: 1025px) {
  .fighters-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
```

## ⚡ Performance

### Otimizações Implementadas

1. **Debounce em Buscas**: 300ms de delay
2. **Lazy Loading**: Carregamento sob demanda
3. **LocalStorage**: Cache de dados não-críticos
4. **CSS Transitions**: Hardware-accelerated
5. **Skeleton Loading**: Percepção de velocidade

### Boas Práticas

```javascript
// ✅ Bom: Debounce em input
const debouncedSearch = debounce(searchFighters, 300);
input.addEventListener("input", debouncedSearch);

// ❌ Ruim: Request a cada tecla
input.addEventListener("input", searchFighters);

// ✅ Bom: Skeleton antes de carregar
showSkeleton("grid");
const data = await api.getData();
displayData(data);

// ❌ Ruim: Tela vazia durante loading
const data = await api.getData();
displayData(data);
```

## 🐛 Debugging

### Console Logs

```javascript
// Em desenvolvimento
if (window.location.hostname === "localhost") {
  console.log("API Response:", data);
  console.log("Form Data:", formData);
}
```

### Error Handling

```javascript
try {
  const data = await api.request("/endpoint");
  return data;
} catch (error) {
  console.error("API Error:", error);
  showToast(error.message || "Erro desconhecido", "error");
  throw error;
}
```

## 🔒 Segurança

### XSS Prevention

```javascript
// Sempre escape HTML
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// Uso
element.innerHTML = escapeHtml(userInput);
```

### CSRF Protection

```javascript
// Token em meta tag
<meta name="csrf-token" content="{{ csrf_token }}">

// Incluir em requests
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
headers['X-CSRF-Token'] = csrfToken;
```

## 📝 TODO: Melhorias Futuras

- [ ] Service Worker para PWA
- [ ] Offline support completo
- [ ] Upload de fotos de lutadores
- [ ] Charts e gráficos (Chart.js)
- [ ] Animações mais elaboradas
- [ ] Keyboard shortcuts globais
- [ ] Accessibility (ARIA labels)
- [ ] Testes E2E (Playwright)

---

**Próximos passos:** [roadmap.md](roadmap.md)
**Melhorias recomendadas:** [melhorias-recomendadas.md](melhorias-recomendadas.md)
