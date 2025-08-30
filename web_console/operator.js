// Spiral OS operator console
const API_URL =
    (typeof window !== 'undefined' && window.WEB_CONSOLE_API_URL) ||
    'http://localhost:8000/glm-command';
const BASE_URL = API_URL.replace(/\/[a-zA-Z_-]+$/, '');
const OFFER_URL = `${BASE_URL}/offer`;
const UPLOAD_URL = `${BASE_URL}/operator/upload`;

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

function uploadFiles(files, metadata = {}, operator = 'overlord') {
    const formData = new FormData();
    for (const file of files) {
        formData.append('files', file);
    }
    formData.append('operator', operator);
    formData.append('metadata', JSON.stringify(metadata));
    return fetch(UPLOAD_URL, {
        method: 'POST',
        body: formData
    }).then(resp => resp.json());
}

export { API_URL, BASE_URL, OFFER_URL, UPLOAD_URL, sendCommand, startStream, uploadFiles };

