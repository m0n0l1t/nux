const API_BASE = '';
let jwtToken = null;
let telegramBotUsername = 'your_bot';  // По умолчанию

// Загружаем конфигурацию бота при старте
async function loadBotConfig() {
    try {
        const response = await fetch('/config/bot');
        if (response.ok) {
            const data = await response.json();
            telegramBotUsername = data.bot_username || 'your_bot';
            updateTelegramBotLink();
        }
    } catch (err) {
        // Silent fail
    }
}

function updateTelegramBotLink() {
    const link = document.getElementById('telegramBotLink');
    if (link) {
        link.href = `https://t.me/${telegramBotUsername}`;
        link.textContent = `Открыть бота @${telegramBotUsername}`;
    }
}

// ========== Утилиты ==========

/**
 * Экранирование HTML для защиты от XSS
 */
function escapeHtml(str) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}

/**
 * Универсальный API клиент с обработкой ошибок
 */
async function apiCall(path, options = {}) {
    const headers = { 'Content-Type': 'application/json' };
    if (jwtToken) headers['Authorization'] = `Bearer ${jwtToken}`;
    
    const response = await fetch(API_BASE + path, { ...options, headers });
    
    // Обработка 401 — токен протух
    if (response.status === 401) {
        logout();
        alert('Сессия истекла. Войдите заново.');
        throw new Error('Unauthorized');
    }
    
    if (!response.ok) {
        const errorText = await response.text();
        try {
            const errorJson = JSON.parse(errorText);
            throw new Error(errorJson.detail || errorText);
        } catch {
            throw new Error(errorText);
        }
    }
    
    // Пустой ответ
    if (response.status === 204) return null;
    
    return response.json();
}

/**
 * Показать индикатор загрузки на элементе
 */
function setLoading(elementId, loading) {
    const el = document.getElementById(elementId);
    if (!el) return;
    if (loading) {
        el.dataset.loading = 'true';
    } else {
        delete el.dataset.loading;
    }
}

// ========== Модальные окна ==========

function showLoginModal() {
    document.getElementById('loginModal').classList.add('active');
    document.getElementById('loginUsername').focus();
}

function showRegisterModal() {
    document.getElementById('registerModal').classList.add('active');
    document.getElementById('regInviteCode').focus();
}

function showTelegramLinkModal() {
    document.getElementById('telegramLinkModal').classList.add('active');
    document.getElementById('telegramCodeResult').classList.add('hidden');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

function switchToRegister(e) {
    e.preventDefault();
    closeModal('loginModal');
    showRegisterModal();
}

function switchToLogin(e) {
    e.preventDefault();
    closeModal('registerModal');
    showLoginModal();
}

// Закрытие по клику вне окна
document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
});

// ========== Навигация ==========

function showApp(username) {
    document.getElementById('landingPage').classList.add('hidden');
    document.getElementById('appView').classList.remove('hidden');
    document.getElementById('userName').textContent = escapeHtml(username);
}

function showLanding() {
    document.getElementById('landingPage').classList.remove('hidden');
    document.getElementById('appView').classList.add('hidden');
}

// ========== Аутентификация ==========

async function login() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    
    if (!username || !password) {
        document.getElementById('loginError').textContent = 'Заполните все поля';
        return;
    }
    
    setLoading('loginBtn', true);
    document.getElementById('loginError').textContent = '';
    
    try {
        const data = await apiCall('/auth/token', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        
        jwtToken = data.access_token;
        localStorage.setItem('jwt', jwtToken);
        localStorage.setItem('username', username);
        
        closeModal('loginModal');
        showApp(username);
        loadBalance();
        loadProxy();
        loadWireGuard();
        loadInvites();
        
        // Очистка формы
        document.getElementById('loginUsername').value = '';
        document.getElementById('loginPassword').value = '';
        document.getElementById('loginError').textContent = '';
    } catch (err) {
        document.getElementById('loginError').textContent = err.message;
    } finally {
        setLoading('loginBtn', false);
    }
}

async function register() {
    const inviteCode = document.getElementById('regInviteCode').value.trim();
    const username = document.getElementById('regUsername').value.trim();
    const password = document.getElementById('regPassword').value;
    
    if (!inviteCode || !username || !password) {
        document.getElementById('registerError').textContent = 'Заполните обязательные поля';
        return;
    }
    
    if (password.length < 6) {
        document.getElementById('registerError').textContent = 'Пароль должен быть не менее 6 символов';
        return;
    }
    
    setLoading('registerBtn', true);
    document.getElementById('registerError').textContent = '';
    
    try {
        await apiCall('/auth/register', {
            method: 'POST',
            body: JSON.stringify({
                invite_code: inviteCode,
                username,
                password
            })
        });
        
        alert('✅ Регистрация успешна! Теперь войдите.');
        closeModal('registerModal');
        showLoginModal();
        
        // Очистка формы
        document.getElementById('regInviteCode').value = '';
        document.getElementById('regUsername').value = '';
        document.getElementById('regPassword').value = '';
        document.getElementById('registerError').textContent = '';
    } catch (err) {
        document.getElementById('registerError').textContent = err.message;
    } finally {
        setLoading('registerBtn', false);
    }
}

function logout() {
    jwtToken = null;
    localStorage.removeItem('jwt');
    localStorage.removeItem('username');
    showLanding();
}

// ========== Привязка Telegram ==========

async function showTelegramLink() {
    showTelegramLinkModal();
}

async function generateTelegramCode() {
    setLoading('generateCodeBtn', true);
    document.getElementById('telegramError').textContent = '';
    
    try {
        const result = await apiCall('/telegram/connect', { method: 'POST' });
        document.getElementById('telegramCode').textContent = result.code;
        document.getElementById('telegramCodeResult').classList.remove('hidden');
    } catch (err) {
        document.getElementById('telegramError').textContent = err.message;
    } finally {
        setLoading('generateCodeBtn', false);
    }
}

// ========== Прокси ==========

async function loadBalance() {
    try {
        const balanceData = await apiCall('/billing/balance');
        const balanceEl = document.getElementById('balanceDisplay');
        if (balanceEl) {
            balanceEl.textContent = `💰 ${balanceData.balance_stars.toFixed(1)} ⭐️`;
        }
    } catch (err) {
        // Silent fail for balance
    }
}

async function loadProxy() {
    try {
        const proxy = await apiCall('/proxy');
        const container = document.getElementById('proxyService');
        const daysLeft = proxy.days_left;
        const proxyLink = proxy.proxy_link || '';

        container.innerHTML = `
            <div class="service">
                <strong>${escapeHtml(proxy.name)}</strong><br>
                Осталось дней: <span class="days">${daysLeft}</span><br>
                ${proxyLink ? `<a href="${escapeHtml(proxyLink)}" class="proxy-link" target="_blank">🔗 Подключиться к NuxTunnel</a>` : '<span class="hint">Ссылка недоступна</span>'}
            </div>
        `;
    } catch (err) {
        document.getElementById('proxyService').innerHTML =
            `<span class="error">Ошибка загрузки NuxTunnel: ${escapeHtml(err.message)}</span>`;
    }
}

// ========== WireGuard ==========

async function loadWireGuard() {
    try {
        const services = await apiCall('/wireguard');
        const container = document.getElementById('wgServicesList');
        container.innerHTML = '';
        
        if (!services.length) {
            container.innerHTML = '<p>Нет услуг NuxGuard. Создайте первую.</p>';
            return;
        }
        
        for (let s of services) {
            const div = document.createElement('div');
            div.className = 'wg-service';
            
            div.innerHTML = `
                <strong>${escapeHtml(s.name)}</strong><br>
                Осталось дней: <span class="days">${s.days_left}</span><br>
                Адрес: <code>${escapeHtml(s.address)}</code><br>
                Публичный ключ: <code>${escapeHtml(s.public_key)}</code>
            `;
            
            // Кнопка скачивания
            const downloadBtn = document.createElement('button');
            downloadBtn.className = 'small';
            downloadBtn.textContent = 'Скачать конфиг';
            downloadBtn.onclick = async () => {
                try {
                    const response = await fetch(`/wireguard/${s.id}/config`, {
                        headers: { 'Authorization': `Bearer ${jwtToken}` }
                    });
                    
                    if (response.ok) {
                        const blob = await response.blob();
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `nuxguard_${escapeHtml(s.name)}.conf`;
                        a.click();
                        URL.revokeObjectURL(url);
                    } else {
                        alert('Ошибка скачивания');
                    }
                } catch (err) {
                    alert('Ошибка: ' + err.message);
                }
            };
            
            // Кнопка удаления
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'small';
            deleteBtn.textContent = 'Удалить';
            deleteBtn.onclick = async () => {
                if (confirm('Удалить услугу?')) {
                    try {
                        await apiCall(`/wireguard/${s.id}`, { method: 'DELETE' });
                        loadWireGuard();
                    } catch (err) {
                        alert('Ошибка удаления: ' + err.message);
                    }
                }
            };
            
            div.appendChild(downloadBtn);
            div.appendChild(deleteBtn);
            container.appendChild(div);
        }
    } catch (err) {
        document.getElementById('wgServicesList').innerHTML = 
            `<span class="error">Ошибка загрузки: ${escapeHtml(err.message)}</span>`;
    }
}

async function createWireguard() {
    const name = document.getElementById('wgName').value.trim();
    
    if (!name) {
        alert('Введите название');
        return;
    }
    
    setLoading('createWgBtn', true);
    
    try {
        await apiCall('/wireguard', {
            method: 'POST',
            body: JSON.stringify({ name })
        });
        
        document.getElementById('createResult').innerHTML = '<span style="color:green">Услуга создана</span>';
        loadWireGuard();
        document.getElementById('wgName').value = '';
        
        setTimeout(() => {
            document.getElementById('createResult').innerHTML = '';
        }, 3000);
    } catch (err) {
        document.getElementById('createResult').innerHTML = 
            `<span class="error">Ошибка: ${escapeHtml(err.message)}</span>`;
    } finally {
        setLoading('createWgBtn', false);
    }
}

// ========== Инвайты ==========

async function loadInvites() {
    try {
        const invites = await apiCall('/invites');
        const container = document.getElementById('invitesList');
        container.innerHTML = '';
        
        if (invites.length === 0) {
            container.innerHTML = '<p>Нет созданных инвайтов.</p>';
            return;
        }
        
        for (let inv of invites) {
            const div = document.createElement('div');
            div.className = 'service';
            
            const used = inv.used_by_user_id 
                ? `✅ Использован (user ${inv.used_by_user_id})` 
                : '🟢 Не использован';
            
            div.innerHTML = `
                <strong>Код:</strong> <code>${escapeHtml(inv.code)}</code><br>
                ${used}<br>
                Создан: ${new Date(inv.created_at).toLocaleString()}
            `;
            
            container.appendChild(div);
        }
    } catch (err) {
        document.getElementById('invitesList').innerHTML = 
            `<span class="error">Ошибка загрузки: ${escapeHtml(err.message)}</span>`;
    }
}

async function createInvite() {
    setLoading('createInviteBtn', true);
    
    try {
        await apiCall('/invites', { method: 'POST' });
        alert('✅ Инвайт создан');
        loadInvites();
    } catch (err) {
        alert('Ошибка: ' + err.message);
    } finally {
        setLoading('createInviteBtn', false);
    }
}

// ========== Обработчики событий ==========

document.getElementById('loginBtn').onclick = login;
document.getElementById('registerBtn').onclick = register;
document.getElementById('logoutBtn').onclick = logout;
document.getElementById('createWgBtn').onclick = createWireguard;
document.getElementById('refreshInvitesBtn').onclick = loadInvites;
document.getElementById('createInviteBtn').onclick = createInvite;
document.getElementById('generateCodeBtn').onclick = generateTelegramCode;

// Enter для логина
document.getElementById('loginPassword').onkeypress = (e) => {
    if (e.key === 'Enter') login();
};

document.getElementById('regPassword').onkeypress = (e) => {
    if (e.key === 'Enter') register();
};

document.getElementById('wgName').onkeypress = (e) => {
    if (e.key === 'Enter') createWireguard();
};

// ESC для закрытия модалок
document.onkeydown = (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal.active').forEach(modal => {
            modal.classList.remove('active');
        });
    }
};

// ========== Инструкции ==========

function openInstructions() {
    document.getElementById('instructionsModal').classList.add('active');
}

function showInstructionTab(tabName) {
    // Скрыть все табы
    document.querySelectorAll('.instruction-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.instructions-tabs .tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Показать нужный таб
    document.getElementById(`instruction-${tabName}`).classList.add('active');
    
    // Активировать кнопку
    const buttons = document.querySelectorAll('.instructions-tabs .tab-btn');
    const tabIndex = { tunnel: 0, guard: 1, payment: 2 }[tabName];
    if (buttons[tabIndex]) buttons[tabIndex].classList.add('active');
}

// ========== Восстановление сессии ==========

const savedToken = localStorage.getItem('jwt');
const savedUsername = localStorage.getItem('username');

if (savedToken && savedUsername) {
    jwtToken = savedToken;
    showApp(savedUsername);
    loadBotConfig();
    loadBalance().catch(() => {});
    loadProxy().catch(() => {});
    loadWireGuard().catch(() => {});
    loadInvites().catch(() => {});
} else {
    showLanding();
    loadBotConfig();
}
