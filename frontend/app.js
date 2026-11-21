const API = "";
let ws = null;
let currentSessionId = null;
let pendingToolConfirm = null;

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    loadConfig();
    loadSkills();
    loadSessions();
    loadProject();
});

function initTabs() {
    document.querySelectorAll(".tab").forEach(tab => {
        tab.addEventListener("click", () => {
            document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
            document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
            tab.classList.add("active");
            document.getElementById(`tab-${tab.dataset.tab}`).classList.add("active");
            if (tab.dataset.tab === "sessions") loadSessions();
            if (tab.dataset.tab === "project") loadProject();
        });
    });

    document.getElementById("send-btn").addEventListener("click", sendMessage);
    document.getElementById("stop-btn").addEventListener("click", stopGeneration);
    document.getElementById("chat-input").addEventListener("keydown", e => {
        if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });
    document.getElementById("new-session-btn").addEventListener("click", () => createSession());
    document.getElementById("new-session-btn-2").addEventListener("click", () => createSession());
    document.getElementById("load-project-btn").addEventListener("click", loadProject);
    document.getElementById("save-agents-btn").addEventListener("click", saveAgentsMd);
    document.getElementById("session-select").addEventListener("change", e => switchSession(parseInt(e.target.value)));
}

async function apiGet(path) {
    const res = await fetch(`${API}${path}`);
    return res.json();
}

async function apiPost(path, data) {
    const res = await fetch(`${API}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });
    return res.json();
}

async function loadConfig() {
    const data = await apiGet("/api/config");
    renderProviders(data.providers, data.active);
}

function renderProviders(providers, activeId) {
    const container = document.getElementById("providers-list");
    container.innerHTML = "";
    providers.forEach(p => {
        const card = document.createElement("div");
        card.className = "provider-card";
        card.innerHTML = `
            <div class="provider-header">
                <h3>${p.label} <span class="badge ${p.is_active ? "active" : "inactive"}">${p.is_active ? "Active" : "Inactive"}</span></h3>
                <span class="badge ${p.has_key ? "active" : "inactive"}">${p.has_key ? "Key Set" : "No Key"}</span>
            </div>
            <div class="provider-fields">
                <div class="field"><label>Base URL</label><input type="text" value="${p.base_url}" data-field="base_url" ${p.is_active ? "" : "disabled"}></div>
                <div class="field"><label>Model</label><input type="text" value="${p.model}" data-field="model" ${p.is_active ? "" : "disabled"}></div>
            </div>
            <div class="provider-fields full">
                <div class="field"><label>API Key</label><input type="password" placeholder="Enter key to save" data-field="key"></div>
            </div>
            <div class="provider-actions">
                ${!p.is_active ? `<button class="btn secondary set-active" data-id="${p.id}">Set Active</button>` : ""}
                <button class="btn primary save-provider" data-id="${p.id}">Save</button>
                <button class="btn secondary test-provider" data-id="${p.id}">Test</button>
                ${p.has_key ? `<button class="btn danger delete-key" data-id="${p.id}">Delete Key</button>` : ""}
            </div>
        `;
        container.appendChild(card);

        card.querySelector(".set-active").addEventListener("click", () => setActiveProvider(p.id));
        card.querySelector(".save-provider").addEventListener("click", () => saveProvider(p.id, card));
        card.querySelector(".test-provider").addEventListener("click", () => testProvider(p.id));
        card.querySelector(".delete-key")?.addEventListener("click", () => deleteKey(p.id));
    });
}

async function setActiveProvider(id) {
    await apiPost("/api/config/provider", { provider_id: id });
    loadConfig();
}

async function saveProvider(id, card) {
    const base_url = card.querySelector('[data-field="base_url"]').value;
    const model = card.querySelector('[data-field="model"]').value;
    await apiPost("/api/config/provider/update", { provider_id: id, base_url, model });
    loadConfig();
}

async function testProvider(id) {
    const btn = document.querySelector(`.test-provider[data-id="${id}"]`);
    btn.disabled = true;
    btn.textContent = "Testing...";
    const res = await apiPost("/api/config/test", { provider_id: id });
    btn.disabled = false;
    btn.textContent = "Test";
    alert(res.success ? "Connection OK" : `Failed: ${res.message}`);
}

async function deleteKey(id) {
    if (confirm("Delete API key?")) {
        await apiPost("/api/config/key/delete", { provider_id: id });
        loadConfig();
    }
}

async function loadSkills() {
    const data = await apiGet("/api/skills");
    renderSkills(data.skills);
}

function renderSkills(skills) {
    const list = document.getElementById("skills-list");
    const detail = document.getElementById("skill-detail");
    list.innerHTML = "";
    skills.forEach(s => {
        const card = document.createElement("div");
        card.className = `skill-card ${s.enabled ? "enabled" : ""}`;
        card.innerHTML = `
            <h4>${s.name}</h4>
            <p>${s.description}</p>
            <div class="skill-meta">
                <span>${s.enabled ? "Enabled" : "Disabled"}</span>
                <span>Click to ${s.enabled ? "disable" : "enable"}</span>
            </div>
        `;
        card.addEventListener("click", () => toggleSkill(s.name, !s.enabled, card));
        card.addEventListener("dblclick", () => showSkillDetail(s));
        list.appendChild(card);
    });
}

async function toggleSkill(name, enable, card) {
    await apiPost("/api/skills/toggle", { name, enable });
    card.classList.toggle("enabled", enable);
    card.querySelector(".skill-meta span").textContent = enable ? "Enabled" : "Disabled";
}

function showSkillDetail(skill) {
    const detail = document.getElementById("skill-detail");
    detail.classList.remove("hidden");
    detail.innerHTML = `<h3>${skill.name}</h3><pre>${skill.skill_md || "No SKILL.md"}</pre>`;
}

async function loadSessions() {
    const data = await apiGet("/api/sessions");
    renderSessions(data.sessions);
    renderSessionSelect(data.sessions);
}

function renderSessions(sessions) {
    const list = document.getElementById("sessions-list");
    list.innerHTML = "";
    sessions.forEach(s => {
        const item = document.createElement("div");
        item.className = "session-item";
        item.innerHTML = `
            <div class="session-info">
                <h4>${s.name}</h4>
                <p>${s.project_dir || "No project"} · Updated ${new Date(s.updated_at).toLocaleString()}</p>
            </div>
            <div class="session-actions">
                <button class="btn secondary resume-btn" data-id="${s.id}">Resume</button>
                <button class="btn secondary rename-btn" data-id="${s.id}">Rename</button>
                <button class="btn danger delete-btn" data-id="${s.id}">Delete</button>
            </div>
        `;
        item.querySelector(".resume-btn").addEventListener("click", () => switchSession(s.id));
        item.querySelector(".rename-btn").addEventListener("click", () => renameSession(s.id, s.name));
        item.querySelector(".delete-btn").addEventListener("click", () => deleteSession(s.id));
        list.appendChild(item);
    });
}

function renderSessionSelect(sessions) {
    const select = document.getElementById("session-select");
    const current = currentSessionId;
    select.innerHTML = "";
    sessions.forEach(s => {
        const opt = document.createElement("option");
        opt.value = s.id;
        opt.textContent = s.name;
        if (s.id === current) opt.selected = true;
        select.appendChild(opt);
    });
    if (!current && sessions.length) {
        switchSession(sessions[0].id);
    }
}

async function createSession() {
    const name = prompt("Session name:", "New Session");
    if (!name) return;
    const res = await apiPost("/api/sessions", { name, project_dir: document.getElementById("project-dir").value });
    loadSessions();
    switchSession(res.id);
}

async function switchSession(id) {
    currentSessionId = id;
    document.getElementById("session-select").value = id;
    document.getElementById("chat-messages").innerHTML = "";
    connectWS(id);
    const data = await apiGet(`/api/sessions/${id}`);
    if (data.messages) {
        data.messages.forEach(msg => renderMessage(msg));
    }
    scrollToBottom();
}

async function renameSession(id, currentName) {
    const name = prompt("New name:", currentName);
    if (name) {
        await apiPost(`/api/sessions/${id}`, { name });
        loadSessions();
    }
}

async function deleteSession(id) {
    if (confirm("Delete session?")) {
        await apiPost(`/api/sessions/${id}`, { _method: "DELETE" });
        loadSessions();
        if (currentSessionId === id) {
            currentSessionId = null;
            document.getElementById("chat-messages").innerHTML = "";
        }
    }
}

function connectWS(sessionId) {
    if (ws) ws.close();
    ws = new WebSocket(`ws://${location.host}/ws/chat/${sessionId}`);
    ws.onmessage = e => {
        const msg = JSON.parse(e.data);
        handleWSMessage(msg);
    };
    ws.onclose = () => setTimeout(() => connectWS(sessionId), 2000);
}

function handleWSMessage(msg) {
    switch (msg.type) {
        case "content":
            appendContent(msg.content);
            break;
        case "tool_start":
            showToolCall(msg.name, msg.id, "pending");
            break;
        case "tool_result":
            updateToolCall(msg.id, msg.result);
            break;
        case "error":
            showError(msg.content);
            break;
        case "done":
            enableInput();
            break;
    }
}

function sendMessage() {
    const input = document.getElementById("chat-input");
    const text = input.value.trim();
    if (!text || !ws || ws.readyState !== WebSocket.OPEN) return;
    input.value = "";
    disableInput();
    addUserMessage(text);
    ws.send(JSON.stringify({ type: "chat", message: text }));
}

function stopGeneration() {
    if (ws) { ws.close(); ws = null; }
    enableInput();
}

function disableInput() {
    document.getElementById("send-btn").disabled = true;
    document.getElementById("stop-btn").disabled = false;
    document.getElementById("chat-input").disabled = true;
}

function enableInput() {
    document.getElementById("send-btn").disabled = false;
    document.getElementById("stop-btn").disabled = true;
    document.getElementById("chat-input").disabled = false;
    document.getElementById("chat-input").focus();
}

function addUserMessage(text) {
    const container = document.getElementById("chat-messages");
    const div = document.createElement("div");
    div.className = "message user";
    div.innerHTML = `<div class="avatar">U</div><div class="message-content"><pre>${escapeHtml(text)}</pre></div>`;
    container.appendChild(div);
    scrollToBottom();
}

function appendContent(text) {
    const container = document.getElementById("chat-messages");
    let last = container.lastElementChild;
    if (!last || last.classList.contains("user")) {
        last = document.createElement("div");
        last.className = "message assistant";
        last.innerHTML = `<div class="avatar">A</div><div class="message-content"></div>`;
        container.appendChild(last);
    }
    last.querySelector(".message-content").textContent += text;
    scrollToBottom();
}

function showToolCall(name, id, status) {
    const container = document.getElementById("chat-messages");
    let last = container.lastElementChild;
    if (!last || last.classList.contains("user")) {
        last = document.createElement("div");
        last.className = "message tool";
        last.innerHTML = `<div class="avatar">T</div><div class="message-content"></div>`;
        container.appendChild(last);
    }
    const toolDiv = document.createElement("div");
    toolDiv.className = `tool-call ${status}`;
    toolDiv.dataset.id = id;
    toolDiv.innerHTML = `<strong>${name}</strong> <span class="status">[${status}]</span>`;
    last.querySelector(".message-content").appendChild(toolDiv);
    scrollToBottom();
}

function updateToolCall(id, result) {
    const toolDiv = document.querySelector(`.tool-call[data-id="${id}"]`);
    if (toolDiv) {
        toolDiv.className = `tool-call ${result.error ? "error" : "done"}`;
        toolDiv.innerHTML = `<strong>${toolDiv.querySelector("strong").textContent}</strong> <span class="status">[${result.error ? "error" : "done"}]</span><pre>${escapeHtml(JSON.stringify(result, null, 2))}</pre>`;
    }
}

function showError(text) {
    const container = document.getElementById("chat-messages");
    const div = document.createElement("div");
    div.className = "message tool";
    div.innerHTML = `<div class="avatar">!</div><div class="message-content"><pre style="color: var(--danger)">${escapeHtml(text)}</pre></div>`;
    container.appendChild(div);
    enableInput();
    scrollToBottom();
}

function scrollToBottom() {
    const container = document.getElementById("chat-messages");
    container.scrollTop = container.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

async function loadProject() {
    const dir = document.getElementById("project-dir").value.trim();
    if (!dir) return;
    const data = await apiGet(`/api/agents-md?project_dir=${encodeURIComponent(dir)}`);
    document.getElementById("agents-md").value = data.content;
}

async function saveAgentsMd() {
    const dir = document.getElementById("project-dir").value.trim();
    const content = document.getElementById("agents-md").value;
    if (!dir) return alert("Set project directory first");
    await apiPost("/api/agents-md", { project_dir: dir, content });
    alert("Saved");
}