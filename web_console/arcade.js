import { BASE_URL } from './main.js';

const CHAKRAS = ['root','sacral','solar','heart','throat','third_eye','crown'];
let lastAligned = null;

function initBar() {
  const bar = document.getElementById('chakra-bar');
  if (!bar) return;
  CHAKRAS.forEach(name => {
    const div = document.createElement('div');
    div.className = 'chakra';
    div.dataset.chakra = name;
    bar.appendChild(div);
  });
}

async function pollStatus() {
  try {
    const resp = await fetch(`${BASE_URL}/chakra/status`);
    const data = await resp.json();
    const beats = data.heartbeats || {};
    const bar = document.getElementById('chakra-bar');
    if (bar) {
      CHAKRAS.forEach(name => {
        const seg = bar.querySelector(`[data-chakra="${name}"]`);
        if (!seg) return;
        const freq = beats[name];
        if (freq) {
          const height = Math.min(40, freq * 20);
          seg.style.height = `${height}px`;
          seg.classList.remove('down');
        } else {
          seg.style.height = '5px';
          seg.classList.add('down');
        }
      });
    }
    if (data.status === 'aligned') {
      lastAligned = new Date().toLocaleTimeString();
      const tsEl = document.getElementById('last-alignment');
      if (tsEl) tsEl.textContent = `Last alignment: ${lastAligned}`;
    }
  } catch (err) {
    console.error('chakra poll error', err);
  } finally {
    setTimeout(pollStatus, 1000);
  }
}

window.addEventListener('load', () => {
  if (!document.getElementById('arcade')) return;
  initBar();
  pollStatus();
});
