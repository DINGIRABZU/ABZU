// Spiral OS web console
// Configuration
const API_URL =
    (typeof process !== 'undefined' && process.env && process.env.WEB_CONSOLE_API_URL) ||
    (typeof window !== 'undefined' && window.WEB_CONSOLE_API_URL) ||
    'http://localhost:8000/glm-command';
const BASE_URL = API_URL.replace(/\/[a-zA-Z_-]+$/, '');
const OFFER_URL = `${BASE_URL}/offer`;

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

document.getElementById('send-btn').addEventListener('click', sendCommand);
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
});
