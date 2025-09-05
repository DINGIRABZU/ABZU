const room = window.location.pathname.split('/').pop();
const wsUrl = `${window.location.origin.replace(/^http/, 'ws')}/agent/chat/${room}`;
const socket = new WebSocket(wsUrl);
const [agentA, agentB] = room.split('-');

document.getElementById('room-title').textContent = `${agentA} ⇄ ${agentB}`;

const senderSel = document.getElementById('sender');
[agentA, agentB, 'operator'].forEach((s) => {
    const opt = document.createElement('option');
    opt.value = s;
    opt.textContent = s;
    senderSel.appendChild(opt);
});

const targetSel = document.getElementById('target');
[agentA, agentB].forEach((t) => {
    const opt = document.createElement('option');
    opt.value = t;
    opt.textContent = t;
    targetSel.appendChild(opt);
});

const messagesEl = document.getElementById('messages');
socket.onmessage = (ev) => {
    try {
        const data = JSON.parse(ev.data);
        const li = document.createElement('li');
        const ts = data.timestamp ? `[${data.timestamp}] ` : '';
        li.textContent = `${ts}${data.sender}→${data.target}: ${data.text}`;
        messagesEl.appendChild(li);
    } catch (err) {
        console.error('bad message', err);
    }
};

function sendMessage() {
    const text = document.getElementById('chat-input').value.trim();
    if (!text) return;
    const sender = senderSel.value;
    const target = targetSel.value;
    socket.send(JSON.stringify({ sender, target, text }));
    document.getElementById('chat-input').value = '';
}

document.getElementById('send-btn').addEventListener('click', sendMessage);
document.getElementById('chat-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});
