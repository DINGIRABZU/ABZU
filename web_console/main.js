// Spiral OS web console
// Configuration
const API_URL =
    (typeof process !== 'undefined' && process.env && process.env.WEB_CONSOLE_API_URL) ||
    (typeof window !== 'undefined' && window.WEB_CONSOLE_API_URL) ||
    'http://localhost:8000/glm-command';
const BASE_URL = API_URL.replace(/\/[a-zA-Z_-]+$/, '');
const OFFER_URL = `${BASE_URL}/offer`;
const STARTUP_LOG_URL = 'logs/nazarick_startup.json';
const REGISTRY_URL = 'agents/nazarick/agent_registry.json';
const EVENTS_URL = `${BASE_URL.replace(/^http/, 'ws')}/operator/events`;
const CONVO_LOG_URL = `${BASE_URL}/conversation/logs`;
const NLQ_LOGS_URL = `${BASE_URL}/nlq/logs`;

const GLYPHS = {
    joy: '🌀😊',
    sadness: '🌀😢',
    anger: '🌀😠',
    fear: '🌀😨',
    neutral: '🌀'
};

let mode = 'crown';
const modeSel = document.createElement('select');
modeSel.id = 'mode-select';
['Crown', 'Nazarick'].forEach((label) => {
    const opt = document.createElement('option');
    opt.value = label.toLowerCase();
    opt.textContent = label;
    modeSel.appendChild(opt);
});
modeSel.addEventListener('change', (e) => {
    mode = e.target.value;
});
const cmdInput = document.getElementById('command-input');
cmdInput.insertAdjacentElement('beforebegin', modeSel);

function applyStyle(style) {
    const video = document.getElementById('avatar');
    let overlay = document.getElementById('style-indicator');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'style-indicator';
        overlay.style.marginTop = '0.5rem';
        video.insertAdjacentElement('afterend', overlay);
    }
    overlay.textContent = style ? `Style: ${style}` : '';
    video.className = style ? `style-${style}` : '';
}

document.getElementById('send-btn').addEventListener('click', () => sendCommand());
document.getElementById('command-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        sendCommand();
    }
});
document.getElementById('command-input').title =
    'Enter natural language commands for any agent.';

document.getElementById('search-btn').addEventListener('click', runSearch);
document.getElementById('global-search').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        runSearch();
    }
});
document.getElementById('global-search').title =
    'Search conversation logs using natural language queries.';

// Music generation elements
const musicContainer = document.createElement('div');
musicContainer.style.marginTop = '1rem';

const musicInput = document.createElement('input');
musicInput.id = 'music-prompt';
musicInput.placeholder = 'Describe music';
musicContainer.appendChild(musicInput);

const musicBtn = document.createElement('button');
musicBtn.id = 'music-btn';
musicBtn.textContent = 'Generate Music';
musicContainer.appendChild(musicBtn);

const feedbackInput = document.createElement('input');
feedbackInput.id = 'music-feedback';
feedbackInput.placeholder = 'Feedback';
feedbackInput.style.marginLeft = '0.5rem';
musicContainer.appendChild(feedbackInput);

const ratingInput = document.createElement('input');
ratingInput.id = 'music-rating';
ratingInput.type = 'number';
ratingInput.min = '0';
ratingInput.max = '5';
ratingInput.placeholder = 'Rating';
ratingInput.style.marginLeft = '0.5rem';
musicContainer.appendChild(ratingInput);

const downloadLink = document.createElement('a');
downloadLink.id = 'music-download';
downloadLink.style.display = 'block';
downloadLink.style.marginTop = '0.5rem';
musicContainer.appendChild(downloadLink);

document.body.appendChild(musicContainer);

const eventLog = document.createElement('pre');
eventLog.id = 'event-log';
eventLog.style.marginTop = '1rem';
document.body.appendChild(eventLog);

const statusPanel = document.createElement('pre');
statusPanel.id = 'status-panel';
statusPanel.style.marginTop = '1rem';
document.body.appendChild(statusPanel);

function connectEvents() {
    try {
        const ws = new WebSocket(EVENTS_URL);
        ws.onmessage = (ev) => {
            eventLog.textContent += `${ev.data}\n`;
        };
    } catch (err) {
        console.error('event stream failed', err);
    }
}

function sendCommand(command, agent) {
    let cmd = command;
    if (!cmd) {
        const input = document.getElementById('command-input');
        cmd = input.value.trim();
        if (!cmd) {
            return;
        }
    }
    let url;
    let options;
    if (mode === 'nazarick') {
        url = `${BASE_URL}/openwebui-chat${agent ? `?channel=${encodeURIComponent(agent)}` : ''}`;
        options = {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ messages: [{ role: 'user', content: cmd }] })
        };
    } else {
        const payload = { command: cmd };
        if (agent) {
            payload.agent = agent;
        }
        url = `${BASE_URL}/glm-command`;
        options = {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        };
    }
    fetch(url, options)
        .then((resp) => resp.json())
        .then((data) => {
            document.getElementById('output').textContent = JSON.stringify(data, null, 2);
            const emotion = data.emotion || 'neutral';
            document.getElementById('emotion').textContent = emotion;
            document.getElementById('glyph').textContent = GLYPHS[emotion] || GLYPHS.neutral;
            if (data.style) {
                applyStyle(data.style);
            }
        })
        .catch((err) => {
            document.getElementById('output').textContent = 'Error: ' + err;
        });
}

function generateMusic() {
    const prompt = musicInput.value.trim();
    if (!prompt) {
        return;
    }
    const feedback = feedbackInput.value.trim();
    const ratingVal = parseFloat(ratingInput.value);
    const payload = { prompt };
    if (feedback) {
        payload.feedback = feedback;
    }
    if (!isNaN(ratingVal)) {
        payload.rating = ratingVal;
    }
    fetch(`${BASE_URL}/music`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
        .then((resp) => resp.json())
        .then((data) => {
            if (data.wav) {
                downloadLink.href = data.wav;
                downloadLink.textContent = 'Download WAV';
            }
        })
        .catch((err) => {
            downloadLink.textContent = 'Error: ' + err;
        });
}

musicBtn.addEventListener('click', generateMusic);

document.getElementById('logs-btn').addEventListener('click', loadLogs);

function loadLogs() {
    fetch('emotion_events.jsonl')
        .then((resp) => resp.text())
        .then((txt) => {
            const pre = document.getElementById('emotion-logs');
            pre.style.display = 'block';
            pre.textContent = txt;
        })
        .catch((err) => {
            const pre = document.getElementById('emotion-logs');
            pre.style.display = 'block';
            pre.textContent = 'Error: ' + err;
        });
}

async function runSearch() {
    const term = document.getElementById('global-search').value.trim();
    if (!term) {
        return;
    }
    try {
        const resp = await fetch(NLQ_LOGS_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: term })
        });
        const data = await resp.json();
        document.getElementById('search-results').textContent = JSON.stringify(
            data.rows,
            null,
            2
        );
        highlightMatches(term);
    } catch (err) {
        document.getElementById('search-results').textContent =
            'Search error: ' + err;
    }
}

function highlightMatches(term) {
    const entries = document.querySelectorAll('.conversation-entry');
    const re = new RegExp(term, 'gi');
    entries.forEach((el) => {
        const raw = el.textContent;
        el.innerHTML = raw.replace(re, (m) => `<mark>${m}</mark>`);
    });
}

function openChat(agent) {
    const peer = prompt(
        `Open chat between ${agent.id} and which agent?`,
        'crown'
    );
    if (!peer) {
        return;
    }
    const name = agent.channel ? agent.channel.replace('#', '') : agent.id;
    const room = `${name}-${peer}`;
    window.open(`/chat/${room}`, '_blank');
}

function sendCommandToAgent(agentId, command) {
    sendCommand(command, agentId);
}

async function loadAgents() {
    try {
        const [registryData, logData] = await Promise.all([
            fetch(REGISTRY_URL).then((r) => r.json()),
            fetch(STARTUP_LOG_URL).then((r) => r.json())
        ]);
        const agents = registryData.agents || [];
        const statusMap = {};
        for (const evt of logData) {
            statusMap[evt.agent] = evt.status;
        }
        const list = document.getElementById('agent-list');
        list.innerHTML = '';
        agents.forEach((agent) => {
            const status = statusMap[agent.id] || 'unknown';
            const li = document.createElement('li');
            li.textContent = `${agent.id} (${agent.channel || ''}) - ${status}`;
            const chatBtn = document.createElement('button');
            chatBtn.textContent = 'Open Chat';
            chatBtn.addEventListener('click', () => openChat(agent));
            const cmdBtn = document.createElement('button');
            cmdBtn.textContent = 'Send Command';
            cmdBtn.addEventListener('click', () => {
                const cmd = prompt(`Command for ${agent.id}`);
                if (cmd) {
                    sendCommandToAgent(agent.id, cmd);
                }
            });
            li.appendChild(chatBtn);
            li.appendChild(cmdBtn);
            list.appendChild(li);
        });
        return agents;
    } catch (err) {
        console.error('Failed to load agents', err);
        return [];
    }
}

async function loadConversationLogs(agentIds) {
    const container = document.getElementById('conversation-timeline');
    container.innerHTML = '';
    for (const id of agentIds) {
        try {
            const resp = await fetch(
                `${CONVO_LOG_URL}?agent=${encodeURIComponent(id)}`
            );
            const data = await resp.json();
            renderTimeline(id, data.logs || data);
        } catch (err) {
            console.error('failed to load logs for', id, err);
        }
    }
}

function renderTimeline(agentId, entries) {
    const container = document.getElementById('conversation-timeline');
    const block = document.createElement('div');
    block.className = 'agent-timeline';
    const title = document.createElement('h3');
    title.textContent = agentId;
    block.appendChild(title);
    const ul = document.createElement('ul');
    entries.forEach((e) => {
        const li = document.createElement('li');
        li.className = 'conversation-entry';
        const text = e.text || e.transcript || JSON.stringify(e);
        const ts = e.timestamp ? `[${e.timestamp}] ` : '';
        li.textContent = ts + text;
        ul.appendChild(li);
    });
    block.appendChild(ul);
    container.appendChild(block);
}

function showOnboarding() {
    if (localStorage.getItem('consoleOnboarded')) {
        return;
    }
    const box = document.createElement('div');
    box.id = 'onboarding';
    box.style.position = 'fixed';
    box.style.top = '1rem';
    box.style.right = '1rem';
    box.style.background = '#fff';
    box.style.border = '1px solid #ccc';
    box.style.padding = '1rem';
    box.style.zIndex = '1000';
    box.innerHTML =
        '<p>Welcome! Use the command box to issue tasks and the search bar to explore past conversations.</p>';
    const btn = document.createElement('button');
    btn.textContent = 'Got it';
    btn.addEventListener('click', () => {
        box.remove();
        localStorage.setItem('consoleOnboarded', '1');
    });
    box.appendChild(btn);
    document.body.appendChild(box);
}

async function startStream() {
    const local = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });

    const pc = new RTCPeerConnection();

    for (const track of local.getAudioTracks()) {
        pc.addTrack(track, local);
    }

    pc.addTransceiver('video');
    pc.addTransceiver('audio');

    pc.ontrack = (ev) => {
        const [stream] = ev.streams;
        if (ev.track.kind === 'video') {
            const video = document.getElementById('avatar');
            if (video.srcObject !== stream) {
                video.srcObject = stream;
            }
        } else if (ev.track.kind === 'audio') {
            const audio = document.getElementById('avatar-audio');
            if (audio.srcObject !== stream) {
                audio.srcObject = stream;
            }
        }
    };

    pc.ondatachannel = (ev) => {
        ev.channel.onmessage = (msg) => {
            try {
                const payload = JSON.parse(msg.data);
                if (payload.transcript) {
                    document.getElementById('transcript').textContent = payload.transcript;
                }
                if (payload.prose) {
                    const n = document.getElementById('narrative');
                    n.textContent += payload.prose;
                }
                if (payload.style) {
                    applyStyle(payload.style);
                }
            } catch (e) {
                document.getElementById('transcript').textContent = msg.data;
            }
        };
    };

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    const resp = await fetch(OFFER_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(pc.localDescription)
    });
    const answer = await resp.json();
    await pc.setRemoteDescription(answer);
}

async function loadMetrics() {
    try {
        const resp = await fetch(`${BASE_URL}/metrics`);
        const text = await resp.text();
        const lines = text
            .split('\n')
            .filter((l) =>
                l.startsWith('service_boot_duration_seconds') ||
                l.startsWith('narrative_throughput_total') ||
                l.startsWith('service_errors_total')
            );
        document.getElementById('status-metrics').textContent = lines.join('\n');
    } catch (err) {
        document.getElementById('status-metrics').textContent = 'Error: ' + err;
    }
}

async function loadStatus() {
    try {
        const resp = await fetch(`${BASE_URL}/operator/status`);
        const data = await resp.json();
        document.getElementById('status-panel').textContent = JSON.stringify(data, null, 2);
    } catch (err) {
        document.getElementById('status-panel').textContent = 'Status error: ' + err;
    }
}

async function fetchBackendStatus() {
    try {
        const resp = await fetch(`${BASE_URL}/status`);
        const data = await resp.json();
        document.getElementById('backend-status').textContent = JSON.stringify(data, null, 2);
    } catch (err) {
        document.getElementById('backend-status').textContent = 'Status error: ' + err;
    }
}

function initArcade() {
    const ignite = document.getElementById('ignite-btn');
    const memory = document.getElementById('memory-btn');
    const handover = document.getElementById('handover-btn');
    const addModel = document.getElementById('add-model-btn');
    const removeModel = document.getElementById('remove-model-btn');
    const updateEthics = document.getElementById('update-ethics-btn');
    const actionResult = document.getElementById('action-result');
    ignite.addEventListener('click', () => {
        fetch(`${BASE_URL}/ignite`, { method: 'POST' });
    });
    memory.addEventListener('click', () => {
        fetch(`${BASE_URL}/memory/query`, { method: 'POST' });
    });
    handover.addEventListener('click', () => {
        fetch(`${BASE_URL}/handover`, { method: 'POST' });
    });
    addModel.addEventListener('click', async () => {
        const name = document.getElementById('add-model-name').value;
        const builtin = document.getElementById('add-model-builtin').value;
        try {
            const resp = await fetch(`${BASE_URL}/operator/models`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, builtin })
            });
            actionResult.textContent = await resp.text();
        } catch (err) {
            actionResult.textContent = 'Add model error: ' + err;
        }
    });
    removeModel.addEventListener('click', async () => {
        const name = document.getElementById('remove-model-name').value;
        try {
            const resp = await fetch(
                `${BASE_URL}/operator/models/${encodeURIComponent(name)}`,
                { method: 'DELETE' }
            );
            actionResult.textContent = await resp.text();
        } catch (err) {
            actionResult.textContent = 'Remove model error: ' + err;
        }
    });
    updateEthics.addEventListener('click', async () => {
        const dir = document.getElementById('ethics-dir').value;
        const url = dir
            ? `${BASE_URL}/ingest-ethics?directory=${encodeURIComponent(dir)}`
            : `${BASE_URL}/ingest-ethics`;
        try {
            const resp = await fetch(url, { method: 'POST' });
            actionResult.textContent = await resp.text();
        } catch (err) {
            actionResult.textContent = 'Update ethics error: ' + err;
        }
    });
    fetchBackendStatus();
}

window.addEventListener('load', () => {
    if (document.getElementById('arcade')) {
        initArcade();
        return;
    }
    showOnboarding();
    startStream();
    loadAgents().then((agents) => loadConversationLogs(agents.map((a) => a.id)));
    loadMetrics();
    connectEvents();
    loadStatus();
    setInterval(loadStatus, 5000);
});

export { BASE_URL, startStream, connectEvents };
