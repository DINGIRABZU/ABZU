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

const GLYPHS = {
    joy: '🌀😊',
    sadness: '🌀😢',
    anger: '🌀😠',
    fear: '🌀😨',
    neutral: '🌀'
};

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
    const payload = { command: cmd };
    if (agent) {
        payload.agent = agent;
    }
    fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
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

function openChat(agent) {
    const name = agent.channel ? agent.channel.replace('#', '') : agent.id;
    window.open(`/chat/${name}`, '_blank');
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
    } catch (err) {
        console.error('Failed to load agents', err);
    }
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

window.addEventListener('load', () => {
    startStream();
    loadAgents();
    loadMetrics();
    connectEvents();
});
