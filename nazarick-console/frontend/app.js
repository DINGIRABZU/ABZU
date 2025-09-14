const agent = 'agent1';
const token = 'demo';
const socket = new WebSocket(`ws://localhost:3001/ws/${agent}?token=${token}`);

socket.onmessage = (ev) => {
  const log = document.getElementById('chat-log');
  log.textContent += ev.data + '\n';
  if (ev.data.startsWith('chakra:')) {
    const freq = parseFloat(ev.data.split(':')[1]);
    pulse(freq);
  }
};

function pulse(freq) {
  const orb = document.getElementById('chakra');
  orb.style.opacity = 0.2 + (freq % 1) * 0.8;
}

document.getElementById('send-btn').onclick = () => {
  const input = document.getElementById('chat-input');
  socket.send(input.value);
  input.value = '';
};

document.getElementById('command').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    socket.send(`/cmd ${e.target.value}`);
    e.target.value = '';
  }
});
