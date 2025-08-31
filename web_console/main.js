// Spiral OS web console
// Configuration
const API_URL =
    (typeof process !== 'undefined' && process.env && process.env.WEB_CONSOLE_API_URL) ||
    (typeof window !== 'undefined' && window.WEB_CONSOLE_API_URL) ||
    'http://localhost:8000/glm-command';
const BASE_URL = API_URL.replace(/\/[a-zA-Z_-]+$/, '');
const OFFER_URL = `${BASE_URL}/offer`;
const STARTUP_LOG_URL = 'logs/nazarick_startup.json';
const REGISTRY_URL = 'agents/nazarick/agent_registry.yaml';

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

function parseRegistry(txt) {
    const agents = [];
    let current = null;
    txt.split(/\r?\n/).forEach((line) => {
        const idMatch = line.match(/^-\s*id:\s*(\S+)/);
        if (idMatch) {
            if (current) {
                agents.push(current);
            }
            current = { id: idMatch[1] };
            return;
        }
        if (!current) {
            return;
        }
        const channelMatch = line.match(/channel:\s*"?([^\"]+)"?/);
        if (channelMatch) {
            current.channel = channelMatch[1];
        }
    });
    if (current) {
        agents.push(current);
    }
    return agents;
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
        const [registryText, logData] = await Promise.all([
            fetch(REGISTRY_URL).then((r) => r.text()),
            fetch(STARTUP_LOG_URL).then((r) => r.json())
        ]);
        const agents = parseRegistry(registryText);
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

    pc.ontrack = (ev) => {
        const [stream] = ev.streams;
        const video = document.getElementById('avatar');
        if (video.srcObject !== stream) {
            video.srcObject = stream;
        }
    };

    pc.ondatachannel = (ev) => {
        ev.channel.onmessage = (msg) => {
            try {
                const payload = JSON.parse(msg.data);
                if (payload.transcript) {
                    document.getElementById('transcript').textContent = payload.transcript;
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

window.addEventListener('load', () => {
    startStream();
    loadAgents();
});
