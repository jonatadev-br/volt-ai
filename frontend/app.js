/* ==========================================================================
   Volt-AI — Frontend Application
   ========================================================================== */

const API = '';
let ws = null;
let currentSessionId = null;
let pendingToolConfirm = null;
let sessionsCache = [];
let providersCache = [];
let skillsCache = {};

// ==========================================================================
// Utility Functions
// ==========================================================================

const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, s => ({'&':'&','<':'<','>':'>','"':'"',"'":'''}[s]));
}

function formatDate(iso) {
    try {
        const d = new Date(iso);
        return d.toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
    } catch { return iso; }
}

function showToast(message, type = 'info') {
    const container = $('#toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${escapeHtml(message)}</span><button class="toast-close" aria-label="Fechar"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg></button>`;
    toast.querySelector('.toast-close').onclick = () => toast.remove();
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
}

function openModal(title, bodyHtml, onConfirm) {
    const modal = $('#confirmModal');
    $('#modalTitle').textContent = title;
    $('#modalBody').innerHTML = bodyHtml;
    modal.showModal();
    const cleanup = () => { modal.close(); modal.querySelector('.modal-confirm').onclick = null; modal.querySelector('.modal-cancel').onclick = null; };
    modal.querySelector('.modal-confirm').onclick = () => { onConfirm(); cleanup(); };
    modal.querySelector('.modal-cancel').onclick = cleanup;
    modal.querySelector('.modal-close').onclick = cleanup;
    modal.querySelector('.modal-backdrop').onclick = cleanup;
}

async function apiGet(path) {
    const res = await fetch(`${API}${path}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

async function apiPost(path, data) {
    const res = await fetch(`${API}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

// ==========================================================================
// Render Functions
// ==========================================================================

function renderSessionList(list) {
    sessionsCache = list;
    const ul = $('#sessionList');
    ul.innerHTML = '';

    if (!list.length) {
        ul.innerHTML = `<li class="empty-state" style="padding: var(--space-6); text-align: center; color: var(--text-muted); font-size: var(--text-sm);">Nenhuma sessão</li>`;
        return;
    }

    list.forEach(s => {
        const li = document.createElement('li');
        li.className = `session-item${currentSessionId === s.id ? ' active' : ''}`;
        li.setAttribute('role', 'option');
        li.setAttribute('aria-selected', currentSessionId === s.id);
        li.innerHTML = `
            <div class="session-item-content">
                <div class="session-item-name">${escapeHtml(s.name)}</div>
                <div class="session-item-meta">
                    <span>${escapeHtml(s.project_dir || '—')}</span>
                    <span>${formatDate(s.updated_at)}</span>
                </div>
            </div>
            <div class="session-item-actions">
                <button class="session-item-action delete-session" data-id="${s.id}" aria-label="Excluir sessão">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
            </div>
        `;
        li.onclick = (e) => {
            if (!e.target.closest('.session-item-action')) switchSession(s.id);
        };
        li.querySelector('.delete-session').onclick = (e) => {
            e.stopPropagation();
            if (confirm(`Excluir sessão "${s.name}"?`)) deleteSession(s.id);
        };
        ul.appendChild(li);
    });
}

function renderProviders(providers, activeId) {
    providersCache = providers;
    const grid = $('#providersGrid');
    grid.innerHTML = '';

    providers.forEach(p => {
        const card = document.createElement('div');
        card.className = 'provider-card';
        card.innerHTML = `
            <div class="provider-header">
                <h3>${escapeHtml(p.label)} <span class="badge ${p.is_active ? 'badge-active' : 'badge-inactive'}">${p.is_active ? 'Ativo' : 'Inativo'}</span></h3>
                <span class="badge ${p.has_key ? 'badge-active' : 'badge-inactive'}">${p.has_key ? 'Chave salva' : 'Sem chave'}</span>
            </div>
            <div class="provider-fields">
                <div class="field"><label>Base URL</label><input type="text" value="${escapeHtml(p.base_url)}" data-field="base_url" ${p.is_active ? '' : 'disabled'} placeholder="https://..."></div>
                <div class="field"><label>Modelo</label><input type="text" value="${escapeHtml(p.model)}" data-field="model" ${p.is_active ? '' : 'disabled'} placeholder="model-name"></div>
            </div>
            <div class="provider-fields full">
                <div class="field"><label>API Key</label><input type="password" placeholder="Digite a chave para salvar" data-field="key" autocomplete="new-password"></div>
            </div>
            <div class="provider-actions">
                ${!p.is_active ? `<button class="btn secondary set-active" data-id="${p.id}">Definir ativo</button>` : ''}
                <button class="btn primary save-provider" data-id="${p.id}">Salvar</button>
                <button class="btn secondary test-provider" data-id="${p.id}">Testar</button>
                ${p.has_key ? `<button class="btn danger delete-key" data-id="${p.id}">Excluir chave</button>` : ''}
            </div>
        `;
        grid.appendChild(card);

        card.querySelector('.set-active')?.onclick = () => setActiveProvider(p.id);
        card.querySelector('.save-provider').onclick = () => saveProvider(p.id, card);
        card.querySelector('.test-provider').onclick = () => testProvider(p.id);
        card.querySelector('.delete-key')?.onclick = () => deleteKey(p.id);
    });
}

function renderSkills(skills, enabled) {
    skillsCache = skills;
    const grid = $('#skillsGrid');
    grid.innerHTML = '';

    Object.entries(skills).forEach(([name, skill]) => {
        const isEnabled = enabled.includes(name);
        const card = document.createElement('div');
        card.className = 'skill-card';
        card.dataset.name = name;
        card.innerHTML = `
            <div class="skill-card-header">
                <span class="skill-card-title">${escapeHtml(name)}</span>
                <label class="toggle" aria-label="${isEnabled ? 'Desativar' : 'Ativar'} ${name}">
                    <input type="checkbox" ${isEnabled ? 'checked' : ''} data-skill="${name}">
                    <span class="toggle-slider"></span>
                </label>
            </div>
            <p class="skill-card-desc">${escapeHtml(skill.manifest?.description || 'Sem descrição')}</p>
            <div class="skill-card-triggers">
                ${(skill.manifest?.triggers || []).map(t => `<span class="trigger-tag">${escapeHtml(t)}</span>`).join('')}
            </div>
        `;
        card.querySelector('input').onchange = (e) => toggleSkill(name, e.target.checked);
        card.onclick = (e) => {
            if (!e.target.closest('.toggle')) showSkillDetail(name, skill);
        };
        grid.appendChild(card);
    });
}

function showSkillDetail(name, skill) {
    const detail = $('#skillDetail');
    detail.classList.remove('hidden');
    detail.innerHTML = `
        <div class="skill-detail-header">
            <h3 class="skill-detail-title">${escapeHtml(name)}</h3>
            <button class="icon-btn" id="closeSkillDetail" aria-label="Fechar detalhes"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg></button>
        </div>
        <div class="skill-detail-content">${escapeHtml(skill.skill_md || 'Sem documentação detalhada.')}</div>
    `;
    $('#closeSkillDetail').onclick = () => detail.classList.add('hidden');
}

function renderSessions(list) {
    const container = $('#sessionsList');
    container.innerHTML = '';

    if (!list.length) {
        container.innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="4" width="18" height="18" rx="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                <h3>Nenhuma sessão</h3>
                <p>Crie sua primeira sessão para começar</p>
            </div>
        `;
        return;
    }

    list.forEach(s => {
        const card = document.createElement('div');
        card.className = 'session-card';
        card.innerHTML = `
            <div class="session-card-main">
                <div class="session-card-name">${escapeHtml(s.name)}</div>
                <div class="session-card-meta">
                    <span>${escapeHtml(s.project_dir || 'Sem diretório')}</span>
                    <span>${formatDate(s.updated_at)}</span>
                    <span>ID: ${s.id}</span>
                </div>
            </div>
            <div class="session-card-actions">
                <button class="btn secondary switch-session" data-id="${s.id}">Entrar</button>
                <button class="btn danger delete-session" data-id="${s.id}" aria-label="Excluir">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
            </div>
        `;
        card.querySelector('.switch-session').onclick = () => switchSession(s.id);
        card.querySelector('.delete-session').onclick = (e) => { e.stopPropagation(); if (confirm(`Excluir sessão "${s.name}"?`)) deleteSession(s.id); };
        container.appendChild(card);
    });
}

function renderChatMessages(messages) {
    const container = $('#chatMessages');
    container.innerHTML = '';

    if (!messages || !messages.length) {
        container.innerHTML = `
            <div class="empty-state" style="padding: var(--space-10);">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                <h3>Nenhuma mensagem</h3>
                <p>Inicie a conversa abaixo</p>
            </div>
        `;
        return;
    }

    messages.forEach(msg => {
        if (msg.role === 'tool') return;
        const div = document.createElement('div');
        div.className = `message ${msg.role}`;
        const avatar = msg.role === 'user' ? 'Você' : 'AI';
        let content = escapeHtml(msg.content || '');
        // Simple markdown-ish rendering for code blocks
        content = content.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code class="lang-$1">$2</code></pre>');
        content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
        div.innerHTML = `
            <div class="message-avatar">${avatar.charAt(0)}</div>
            <div class="message-content">
                <div class="message-bubble">${content}</div>
            </div>
        `;
        container.appendChild(div);
    });
    container.scrollTop = container.scrollHeight;
}

function appendStreamingMessage(role, text) {
    const container = $('#chatMessages');
    let lastMsg = container.querySelector(`.message.${role}.message-streaming`);
    if (!lastMsg) {
        lastMsg = document.createElement('div');
        lastMsg.className = `message ${role} message-streaming`;
        const avatar = role === 'user' ? 'Você' : 'AI';
        lastMsg.innerHTML = `
            <div class="message-avatar">${avatar.charAt(0)}</div>
            <div class="message-content"><div class="message-bubble"></div></div>
        `;
        container.appendChild(lastMsg);
    }
    lastMsg.querySelector('.message-bubble').textContent = text;
    container.scrollTop = container.scrollHeight;
}

function addToolCall(name, args, result) {
    const container = $('#chatMessages');
    const div = document.createElement('div');
    div.className = 'message assistant';
    div.innerHTML = `
        <div class="message-avatar">AI</div>
        <div class="message-content">
            <div class="message-tool">
                <div class="message-tool-header">Ferramenta: <span class="message-tool-name">${escapeHtml(name)}</span></div>
                <div class="message-tool-args">${escapeHtml(JSON.stringify(args, null, 2))}</div>
            </div>
            <div class="message-bubble" style="margin-top: var(--space-2);">${escapeHtml(typeof result === 'object' ? JSON.stringify(result, null, 2) : String(result))}</div>
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function setCurrentSessionUI(session) {
    $('#currentSessionName').textContent = session?.name || 'Nova sessão';
    $('#currentSessionModel').textContent = 'NVIDIA NIM · llama-3.3-70b'; // TODO: from active provider
    // Update session list active state
    $$('#sessionList .session-item').forEach(li => {
        li.classList.toggle('active', li.querySelector('[data-id]')?.dataset.id == session?.id);
        li.setAttribute('aria-selected', li.querySelector('[data-id]')?.dataset.id == session?.id);
    });
}

// ==========================================================================
// API Actions
// ==========================================================================

async function loadConfig() {
    try {
        const data = await apiGet('/api/config');
        renderProviders(data.providers, data.active);
        $('#currentSessionModel').textContent = `${data.providers.find(p => p.id === data.active)?.label || 'NVIDIA NIM'} · ${data.providers.find(p => p.id === data.active)?.model || 'llama-3.3-70b'}`;
    } catch (e) { showToast('Erro ao carregar config: ' + e.message, 'error'); }
}

async function loadSkills() {
    try {
        const data = await apiGet('/api/skills');
        const config = await apiGet('/api/config');
        renderSkills(data.skills.reduce((o, s) => { o[s.name] = s; return o; }, {}), config.skills);
    } catch (e) { showToast('Erro ao carregar skills: ' + e.message, 'error'); }
}

async function loadSessions() {
    try {
        const data = await apiGet('/api/sessions');
        renderSessionList(data.sessions);
        renderSessions(data.sessions);
    } catch (e) { showToast('Erro ao carregar sessões: ' + e.message, 'error'); }
}

async function loadProject() {
    try {
        const dir = $('#projectDir').value || '';
        const data = await apiGet(`/api/agents-md?project_dir=${encodeURIComponent(dir)}`);
        $('#agentsMd').value = data.content;
    } catch (e) { showToast('Erro ao carregar projeto: ' + e.message, 'error'); }
}

async function createSession() {
    try {
        const name = prompt('Nome da sessão:') || 'Nova Sessão';
        const data = await apiPost('/api/sessions', { name, project_dir: $('#projectDir').value || '' });
        await loadSessions();
        await switchSession(data.id);
    } catch (e) { showToast('Erro ao criar sessão: ' + e.message, 'error'); }
}

async function switchSession(id) {
    try {
        const session = await apiGet(`/api/sessions/${id}`);
        currentSessionId = id;
        setCurrentSessionUI(session);
        renderChatMessages(session.messages);
        connectWS(id);
        // Close mobile sessions panel
        $('#chatSessions')?.classList.remove('open');
        $('#chatSessionsOverlay')?.classList.remove('visible');
    } catch (e) { showToast('Erro ao mudar sessão: ' + e.message, 'error'); }
}

async function deleteSession(id) {
    try {
        await apiPost(`/api/sessions/${id}`, { _method: 'DELETE' });
        await loadSessions();
        if (currentSessionId === id) {
            currentSessionId = null;
            setCurrentSessionUI(null);
            renderChatMessages([]);
            disconnectWS();
        }
    } catch (e) { showToast('Erro ao excluir sessão: ' + e.message, 'error'); }
}

async function setActiveProvider(id) {
    try {
        await apiPost('/api/config/provider', { provider_id: id });
        await loadConfig();
        showToast('Provedor ativo alterado');
    } catch (e) { showToast('Erro: ' + e.message, 'error'); }
}

async function saveProvider(id, card) {
    try {
        const base_url = card.querySelector('[data-field="base_url"]').value;
        const model = card.querySelector('[data-field="model"]').value;
        await apiPost('/api/config/provider/update', { provider_id: id, base_url, model });
        await loadConfig();
        showToast('Provedor salvo');
    } catch (e) { showToast('Erro: ' + e.message, 'error'); }
}

async function testProvider(id) {
    try {
        const { success, message } = await apiPost('/api/config/test', { provider_id: id });
        showToast(message, success ? 'success' : 'error');
    } catch (e) { showToast('Erro no teste: ' + e.message, 'error'); }
}

async function deleteKey(id) {
    if (!confirm('Excluir a chave de API?')) return;
    try {
        await apiPost('/api/config/key/delete', { provider_id: id });
        await loadConfig();
        showToast('Chave excluída');
    } catch (e) { showToast('Erro: ' + e.message, 'error'); }
}

async function toggleSkill(name, enable) {
    try {
        await apiPost('/api/skills/toggle', { name, enable });
        await loadSkills();
        showToast(`Skill ${enable ? 'ativada' : 'desativada'}`);
    } catch (e) { showToast('Erro: ' + e.message, 'error'); }
}

async function saveAgentsMd() {
    try {
        const dir = $('#projectDir').value;
        const content = $('#agentsMd').value;
        await apiPost('/api/agents-md', { project_dir: dir, content });
        showToast('AGENTS.md salvo');
    } catch (e) { showToast('Erro ao salvar: ' + e.message, 'error'); }
}

// ==========================================================================
// WebSocket Chat
// ==========================================================================

function connectWS(sessionId) {
    disconnectWS();
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${proto}//${location.host}/ws/chat/${sessionId}`);

    ws.onopen = () => updateConnectionStatus(true);
    ws.onclose = () => { updateConnectionStatus(false); setTimeout(() => connectWS(sessionId), 3000); };
    ws.onerror = () => updateConnectionStatus(false);

    ws.onmessage = (event) => {
        try {
            const chunk = JSON.parse(event.data);
            handleWSChunk(chunk);
        } catch (e) { console.error('WS parse error', e); }
    };
}

function disconnectWS() {
    if (ws) { ws.close(); ws = null; }
    updateConnectionStatus(false);
}

function updateConnectionStatus(connected) {
    const el = $('#connectionStatus');
    if (!el) return;
    el.querySelector('.status-dot').style.background = connected ? 'var(--color-success)' : 'var(--color-destructive)';
    el.querySelector('.status-text').textContent = connected ? 'Conectado' : 'Desconectado';
}

function handleWSChunk(chunk) {
    switch (chunk.type) {
        case 'content':
            appendStreamingMessage('assistant', chunk.content);
            break;
        case 'tool_start':
            // Could show "thinking" indicator
            break;
        case 'tool_result':
            finalizeAssistantMessage();
            addToolCall(chunk.name, chunk.result, chunk.result);
            break;
        case 'done':
            finalizeAssistantMessage();
            break;
        case 'error':
            finalizeAssistantMessage();
            showToast(chunk.content, 'error');
            setInputDisabled(false);
            break;
    }
}

function finalizeAssistantMessage() {
    const streaming = $('#chatMessages .message-streaming');
    if (streaming) streaming.classList.remove('message-streaming');
}

function sendMessage() {
    const input = $('#chatInput');
    const text = input.value.trim();
    if (!text || !ws || ws.readyState !== WebSocket.OPEN) return;

    // Show user message immediately
    const container = $('#chatMessages');
    const empty = container.querySelector('.empty-state');
    if (empty) empty.remove();

    const div = document.createElement('div');
    div.className = 'message user';
    div.innerHTML = `
        <div class="message-avatar">V</div>
        <div class="message-content"><div class="message-bubble">${escapeHtml(text)}</div></div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;

    input.value = '';
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 200) + 'px';

    ws.send(JSON.stringify({ type: 'chat', message: text }));
    setInputDisabled(true);
}

function stopGeneration() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'stop' }));
    }
    setInputDisabled(false);
}

function setInputDisabled(disabled) {
    $('#sendBtn').disabled = disabled;
    $('#stopBtn').style.display = disabled ? 'inline-flex' : 'none';
    $('#chatInput').disabled = disabled;
}

// ==========================================================================
// UI Interactions
// ==========================================================================

function initTabs() {
    $$('.nav-item').forEach(btn => {
        btn.onclick = () => {
            const tab = btn.dataset.tab;
            $$('.nav-item').forEach(b => { b.classList.remove('active'); b.setAttribute('aria-selected', 'false'); });
            $$('.panel').forEach(p => p.classList.remove('active'));
            btn.classList.add('active');
            btn.setAttribute('aria-selected', 'true');
            $('#panel-' + tab).classList.add('active');
            $('#pageTitle').textContent = tab.charAt(0).toUpperCase() + tab.slice(1);
            // Load data on first visit
            if (tab === 'sessions') loadSessions();
            if (tab === 'project') loadProject();
            // Close mobile sidebar
            $('#sidebar')?.classList.remove('open');
            $('#sidebarOverlay')?.classList.remove('visible');
        };
    });
}

function initMobile() {
    // Sidebar toggle
    const sidebar = $('#sidebar');
    const sidebarToggle = $('#sidebarToggle');
    const mobileMenuBtn = $('#mobileMenuBtn');
    let sidebarOverlay = $('#sidebarOverlay');
    if (!sidebarOverlay) {
        sidebarOverlay = document.createElement('div');
        sidebarOverlay.id = 'sidebarOverlay';
        sidebarOverlay.className = 'sidebar-overlay';
        document.body.appendChild(sidebarOverlay);
    }

    function openSidebar() { sidebar.classList.add('open'); sidebarOverlay.classList.add('visible'); mobileMenuBtn.setAttribute('aria-expanded', 'true'); }
    function closeSidebar() { sidebar.classList.remove('open'); sidebarOverlay.classList.remove('visible'); mobileMenuBtn.setAttribute('aria-expanded', 'false'); }

    sidebarToggle?.onclick = closeSidebar;
    mobileMenuBtn?.onclick = () => sidebar.classList.contains('open') ? closeSidebar() : openSidebar();
    sidebarOverlay.onclick = closeSidebar;

    // Chat sessions panel toggle
    const chatSessions = $('#chatSessions');
    let chatSessionsOverlay = $('#chatSessionsOverlay');
    if (!chatSessionsOverlay) {
        chatSessionsOverlay = document.createElement('div');
        chatSessionsOverlay.id = 'chatSessionsOverlay';
        chatSessionsOverlay.className = 'chat-sessions-overlay';
        document.body.appendChild(chatSessionsOverlay);
    }

    $('#newSessionBtn')?.onclick = createSession;
    $('#newSessionBtn2')?.onclick = createSession;

    // Resize handler
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            if (window.innerWidth > 768) {
                closeSidebar();
                chatSessions?.classList.remove('open');
                chatSessionsOverlay?.classList.remove('visible');
            }
        }, 100);
    });
}

function initChatInput() {
    const input = $('#chatInput');
    const form = $('#chatInputForm');

    input.addEventListener('input', () => {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 200) + 'px';
    });

    input.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    form.onsubmit = e => { e.preventDefault(); sendMessage(); };

    $('#sendBtn').onclick = sendMessage;
    $('#stopBtn').onclick = stopGeneration;
    $('#clearChatBtn').onclick = () => { if (confirm('Limpar todo o histórico desta sessão?')) { currentSessionId && switchSession(currentSessionId); } };
    $('#loadProjectBtn').onclick = loadProject;
    $('#saveAgentsBtn').onclick = saveAgentsMd;
}

function initThemeToggle() {
    const toggle = $('#themeToggle');
    const html = document.documentElement;
    const saved = localStorage.getItem('theme') || 'dark';
    html.setAttribute('data-theme', saved);

    toggle.onclick = () => {
        const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        html.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
    };
}

// ==========================================================================
// Initialization
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initMobile();
    initChatInput();
    initThemeToggle();
    loadConfig();
    loadSkills();
    loadSessions();
    loadProject();
});