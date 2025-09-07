import React from 'https://esm.sh/react@18';
import { BASE_URL } from '../main.js';

export default function ChakraPulse() {
  const [chakras, setChakras] = React.useState({});
  const [aligned, setAligned] = React.useState(false);
  const [history, setHistory] = React.useState([]);
  const [resonance, setResonance] = React.useState(false);

  React.useEffect(() => {
    let timer;
    const poll = async () => {
      try {
        const resp = await fetch(`${BASE_URL}/chakra/status`);
        const data = await resp.json();
        setChakras(data.heartbeats || {});
        setAligned(data.status === 'aligned');
        if (data.event === 'great_spiral') {
          setResonance(true);
          setHistory((h) => [...h, new Date().toISOString()]);
          setTimeout(() => setResonance(false), 1000);
        }
      } catch (err) {
        console.error('chakra status error', err);
      }
      timer = setTimeout(poll, 1000);
    };
    poll();
    return () => clearTimeout(timer);
  }, []);

  return React.createElement(
    'div',
    { id: 'chakra-pulse' },
    resonance && React.createElement('div', { className: 'resonance' }),
    React.createElement(
      'div',
      { className: 'orbs' },
      Object.entries(chakras).map(([name, freq]) => {
        const size = 20 + freq * 10;
        const color = `hsl(${Math.min(120, freq * 40)}, 100%, 50%)`;
        const duration = `${Math.max(0.5, 2 / Math.max(freq, 0.1))}s`;
        return React.createElement('div', {
          key: name,
          className: `orb${aligned ? ' aligned' : ''}`,
          style: {
            width: size,
            height: size,
            background: color,
            animation: `pulse ${duration} infinite alternate`
          },
          title: `${name}: ${freq.toFixed(2)}Hz`
        });
      })
    ),
    React.createElement(
      'ul',
      { className: 'history' },
      history.map((t, i) => React.createElement('li', { key: i }, t))
    )
  );
}
