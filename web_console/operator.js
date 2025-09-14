// Spiral OS operator console
const API_URL =
    (typeof window !== 'undefined' && window.WEB_CONSOLE_API_URL) ||
    'http://localhost:8000/glm-command';
const BASE_URL = API_URL.replace(/\/[a-zA-Z_-]+$/, '');
const AGENT =
    (typeof window !== 'undefined' && window.WEB_CONSOLE_AGENT) ||
    'agent';
const OFFER_URL = `${BASE_URL}/${AGENT}/offer`;
const UPLOAD_URL = `${BASE_URL}/operator/upload`;
const STORY_STREAM_URL = `${BASE_URL}/story/stream`;

function sendCommand(cmd) {
    return fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: cmd })
    }).then((resp) => resp.json());
}

async function startStream(videoElem, audioElem, narrativeElem) {
    const pc = new RTCPeerConnection();

    pc.addTransceiver('video');
    pc.addTransceiver('audio');

    pc.ontrack = (ev) => {
        const [stream] = ev.streams;
        if (ev.track.kind === 'video' && videoElem && videoElem.srcObject !== stream) {
            videoElem.srcObject = stream;
        }
        if (ev.track.kind === 'audio' && audioElem && audioElem.srcObject !== stream) {
            audioElem.srcObject = stream;
        }
    };

    pc.ondatachannel = (ev) => {
        ev.channel.onmessage = (msg) => {
            if (!narrativeElem) {
                return;
            }
            try {
                const payload = JSON.parse(msg.data);
                if (payload.prose) {
                    narrativeElem.textContent += payload.prose;
                } else {
                    narrativeElem.textContent += msg.data;
                }
            } catch {
                narrativeElem.textContent += msg.data;
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

    return pc;
}

function connectNarrativeStream(narrativeElem) {
    fetch(STORY_STREAM_URL)
        .then((resp) => {
            const reader = resp.body.getReader();
            const decoder = new TextDecoder();
            let buf = '';
            function pump() {
                return reader.read().then(({ value, done }) => {
                    if (done) {
                        return;
                    }
                    buf += decoder.decode(value, { stream: true });
                    const lines = buf.split('\n');
                    buf = lines.pop();
                    for (const line of lines) {
                        if (!line.trim()) {
                            continue;
                        }
                        narrativeElem.textContent += line + '\n';
                    }
                    return pump();
                });
            }
            return pump();
        })
        .catch((err) => console.error('narrative stream failed', err));
}

function uploadFiles(files = [], metadata = {}, operator = 'overlord') {
    const formData = new FormData();
    for (const file of files) {
        formData.append('files', file);
    }
    formData.append('operator', operator);
    formData.append('metadata', JSON.stringify(metadata));
    // Crown relays metadata and stored paths to RAZAR on success.
    return fetch(UPLOAD_URL, {
        method: 'POST',
        body: formData
    }).then(resp => resp.json());
}

function uploadFile(file, metadata = {}, operator = 'overlord') {
    return uploadFiles([file], metadata, operator);
}

function uploadMedia(blob, filename, metadata = {}, operator = 'overlord') {
    const formData = new FormData();
    formData.append('files', blob, filename);
    formData.append('operator', operator);
    formData.append('metadata', JSON.stringify(metadata));
    return fetch(UPLOAD_URL, { method: 'POST', body: formData }).then(resp => resp.json());
}

export {
    API_URL,
    BASE_URL,
    OFFER_URL,
    UPLOAD_URL,
    STORY_STREAM_URL,
    sendCommand,
    startStream,
    connectNarrativeStream,
    uploadFiles,
    uploadFile,
    uploadMedia
};

