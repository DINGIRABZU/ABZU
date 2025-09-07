import React from 'https://esm.sh/react@18';
import { BASE_URL } from '../../main.js';

export default function ChakraStatusPanel({ initialData }) {
  const [data, setData] = React.useState(initialData || { heartbeats: {}, components: {} });

  React.useEffect(() => {
    let timer;
    const poll = async () => {
      try {
        const resp = await fetch(`${BASE_URL}/chakra/status`);
        const json = await resp.json();
        setData(json);
      } catch (err) {
        console.error('chakra status panel error', err);
      }
      timer = setTimeout(poll, 2000);
    };
    poll();
    return () => clearTimeout(timer);
  }, []);

  return React.createElement(
    'div',
    { id: 'chakra-status-panel' },
    React.createElement(
      'div',
      { className: 'orbs' },
      Object.entries(data.heartbeats || {}).map(([name, freq]) => {
        const size = 20 + freq * 10;
        const duration = `${Math.max(0.5, 2 / Math.max(freq, 0.1))}s`;
        const color = `hsl(${Math.min(120, freq * 40)}, 100%, 50%)`;
        return React.createElement('div', {
          key: name,
          className: 'orb',
          style: { width: size, height: size, background: color, animation: `pulse ${duration} infinite alternate` },
          title: `${name}: ${freq.toFixed(2)}Hz`
        });
      })
    ),
    React.createElement(
      'ul',
      { className: 'components' },
      Object.entries(data.components || {}).map(([name, ver]) =>
        React.createElement('li', { key: name }, `${name} ${ver}`)
      )
    )
  );
}
