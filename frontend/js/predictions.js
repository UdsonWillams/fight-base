// Predictions & Gamification Module

async function initPredictionsSection() {
    if (!requireAuth()) return;
    await Promise.all([
        loadGlobalRankings('all'),
        loadAchievements()
    ]);
}

async function loadGlobalRankings(type = 'all') {
    const container = document.getElementById("rankingsContainer");

    try {
        container.innerHTML = createSkeletonCards(5, "ranking");

        // Em um sistema real, o backend filtraria por mensal/geral
        // Por enquanto, usamos o endpoint de leaderboard que criamos
        // Placeholder: simulando busca global
        const users = [
            { id: 1, avatar: '🐉', username: '@alex_silva', total_points: 1250, events: 12, accuracy: '78%' },
            { id: 2, avatar: '🥋', username: '@mma_master', total_points: 1180, events: 10, accuracy: '72%' },
            { id: 3, avatar: '🦍', username: '@beast_mode', total_points: 1150, events: 15, accuracy: '65%' },
            { id: 4, avatar: '🐺', username: '@wolf_pack', total_points: 1050, events: 8, accuracy: '82%' },
            { id: 5, avatar: '🦅', username: '@eagle_eye', total_points: 980, events: 11, accuracy: '70%' },
        ];

        renderLeaderboard(users, container);
    } catch (error) {
        console.error("Erro ao carregar rankings:", error);
        container.innerHTML = `<div class="empty-state">❌ Erro ao carregar dados</div>`;
    }
}

function renderLeaderboard(users, container) {
    if (!users || users.length === 0) {
        container.innerHTML = `<div class="empty-state">📊 Nenhum Dado</div>`;
        return;
    }

    container.innerHTML = `
        <table class="leaderboard-table">
            <thead>
                <tr>
                    <th class="leaderboard-cell">Rank</th>
                    <th class="leaderboard-cell">Usuário</th>
                    <th class="leaderboard-cell">Eventos</th>
                    <th class="leaderboard-cell">Precisão</th>
                    <th class="leaderboard-cell">Pontos</th>
                </tr>
            </thead>
            <tbody>
                ${users.map((u, i) => `
                    <tr class="leaderboard-row">
                        <td class="leaderboard-cell">
                            <div class="rank-badge rank-${i + 1}">${i + 1}</div>
                        </td>
                        <td class="leaderboard-cell">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="font-size: 1.5rem;">${u.avatar || '👤'}</span>
                                <span style="font-weight: 600;">${escapeHTML(u.username)}</span>
                            </div>
                        </td>
                        <td class="leaderboard-cell">${u.events || 0}</td>
                        <td class="leaderboard-cell text-success">${u.accuracy || '0%'}</td>
                        <td class="leaderboard-cell">
                            <span class="badge badge-primary">${u.total_points} pts</span>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

async function loadAchievements() {
    const container = document.getElementById("rankingsContainer");
    if (!container) return;

    // Criar seção de achievements se não existir
    let achSection = document.getElementById("achievementsSection");
    if (!achSection) {
        achSection = document.createElement("div");
        achSection.id = "achievementsSection";
        achSection.innerHTML = `
            <div class="section-header" style="margin-top: 40px;">
                <h2>🏅 Conquistas Desbloqueadas</h2>
            </div>
            <div id="achievementsGrid" class="achievement-grid"></div>
        `;
        container.parentNode.appendChild(achSection);
    }

    const grid = document.getElementById("achievementsGrid");

    try {
        grid.innerHTML = createSkeletonCards(4, "achievement");

        // Buscar achievements do usuário e definições globais
        const [myAchievements, allAchievements] = await Promise.all([
            api.getAchievements(),
            // Mock de definições se o backend não retornar tudo
            Promise.resolve([
                { code: 'FIRST_PREDICTION', name: 'O Ponto de Partida', description: 'Realizou seu primeiro palpite.', icon: '🔮', category: 'milestone' },
                { code: 'PREDICTIONS_10', name: 'Analista em Ascensão', description: 'Realizou 10 palpites.', icon: '📈', category: 'milestone' },
                { code: 'STREAK_3', name: 'No Calor do Momento', description: 'Acertou 3 palpites seguidos.', icon: '🔥', category: 'streak' },
                { code: 'UNDERDOG_HUNTER', name: 'Caçador de Azarões', description: 'Acertou um vencedor com menos de 30% de chance.', icon: '🐺', category: 'special' }
            ])
        ]);

        const unlockedCodes = new Set(myAchievements.map(a => a.code));

        grid.innerHTML = allAchievements.map(ach => {
            const isUnlocked = unlockedCodes.has(ach.code);
            return `
                <div class="achievement-card ${isUnlocked ? 'unlocked' : ''} category-${ach.category}">
                    <span class="achievement-icon">${ach.icon}</span>
                    <div class="achievement-name">${escapeHTML(ach.name)}</div>
                    <div class="achievement-desc">${escapeHTML(ach.description)}</div>
                </div>
            `;
        }).join('');

    } catch (error) {
        console.error("Erro ao carregar achievements:", error);
        grid.innerHTML = `<div class="empty-state">❌ Erro ao carregar conquistas</div>`;
    }
}

function showAchievementUnlocked(achievement) {
    // Disparar confetti
    if (typeof confetti === 'function') {
        confetti({
            particleCount: 150,
            spread: 70,
            origin: { y: 0.6 },
            colors: ['#6366f1', '#a855f7', '#fbbf24']
        });
    }

    // Mostrar toast customizado
    const toast = document.createElement('div');
    toast.className = 'achievement-toast just-unlocked';
    toast.innerHTML = `
        <div class="achievement-icon" style="font-size: 2rem;">${achievement.icon}</div>
        <div>
            <div style="font-weight: 800; color: #fbbf24;">CONQUISTA DESBLOQUEADA!</div>
            <div style="font-weight: 600;">${escapeHTML(achievement.name)}</div>
        </div>
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 500);
    }, 5000);
}

// Leagues UI
async function loadMyLeagues() {
    const container = document.getElementById("leaguesList");
    try {
        const leagues = await api.getMyLeagues();
        if (!leagues || leagues.length === 0) {
            container.innerHTML = `
                <div class="empty-state glass-card" style="grid-column: 1/-1; padding: 3rem;">
                    <p>Você ainda não está em nenhuma liga.</p>
                    <p class="text-muted">Crie sua própria liga ou entre em uma de seus amigos!</p>
                </div>
            `;
            return;
        }

        container.innerHTML = leagues.map(l => `
            <div class="glass-card league-card" style="padding: 1.5rem; border-radius: 16px;">
                <h3 style="margin-top: 0;">${escapeHTML(l.name)}</h3>
                <p class="text-muted" style="font-size: 0.9rem;">${l.members_count} Membros</p>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem;">
                    <span class="badge">COD: ${escapeHTML(l.invite_code)}</span>
                    <button class="btn btn-sm btn-outline">Ver Ranking</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error("Erro ao carregar ligas:", error);
    }
}

// Modal functions
function showCreateLeagueModal() {
    showToast("Função de criar liga em breve!", "info");
}

function showJoinLeagueModal() {
    showToast("Função de entrar em liga em breve!", "info");
}

// Helper para Renderizar Odds ML
function renderMLOdds(fight) {
    if (!fight.fighter1_probability) return '';

    const prob1 = Math.round(fight.fighter1_probability * 100);
    const prob2 = 100 - prob1;

    return `
        <div class="odds-container">
            <div class="odds-label">
                <span><span class="ml-tag">AI ADVICE</span> ${escapeHTML(fight.fighter1?.name || 'Lutador 1')}</span>
                <span>${escapeHTML(fight.fighter2?.name || 'Lutador 2')}</span>
            </div>
            <div class="odds-bar-bg">
                <div class="odds-fill-f1" style="width: ${prob1}%"></div>
                <div class="odds-fill-f2" style="width: ${prob2}%"></div>
            </div>
            <div class="odds-label" style="margin-top: 4px;">
                <span>${prob1}%</span>
                <span>${prob2}%</span>
            </div>
        </div>
    `;
}
