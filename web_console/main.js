// Spiral OS web console
// Configuration
const API_URL =
    (typeof process !== 'undefined' && process.env && process.env.WEB_CONSOLE_API_URL) ||
    (typeof window !== 'undefined' && window.WEB_CONSOLE_API_URL) ||
    'http://localhost:8000/glm-command';
const BASE_URL = API_URL.replace(/\/[a-zA-Z_-]+$/, '');
const OFFER_URL = `${BASE_URL}/offer`;

document.getElementById('send-btn').addEventListener('click', sendCommand);
document.getElementById('command-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        sendCommand();
    }
});

function sendCommand() {
    const input = document.getElementById('command-input');
    const command = input.value.trim();
    if (!command) {
        return;
    }

    fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command })
    })
        .then((resp) => resp.json())
        .then((data) => {
            document.getElementById('output').textContent = JSON.stringify(data, null, 2);
        })
        .catch((err) => {
            document.getElementById('output').textContent = 'Error: ' + err;
        });
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
            document.getElementById('transcript').textContent = msg.data;
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
});
