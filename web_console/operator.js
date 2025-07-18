// Spiral OS operator console
const API_URL =
    (typeof window !== 'undefined' && window.WEB_CONSOLE_API_URL) ||
    'http://localhost:8000/glm-command';
const BASE_URL = API_URL.replace(/\/[a-zA-Z_-]+$/, '');
const OFFER_URL = `${BASE_URL}/offer`;

function sendCommand(cmd) {
    return fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: cmd })
    }).then(resp => resp.json());
}

async function startStream(videoElem) {
    const pc = new RTCPeerConnection();
    pc.ontrack = (ev) => {
        const [stream] = ev.streams;
        if (videoElem.srcObject !== stream) {
            videoElem.srcObject = stream;
        }
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

    return pc;
}

export { API_URL, BASE_URL, OFFER_URL, sendCommand, startStream };

