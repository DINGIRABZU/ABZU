import React from 'https://esm.sh/react@18';
import { BASE_URL } from '../main.js';

export default function SelfHealingPanel() {
  const [gaps, setGaps] = React.useState({});
  const [agents, setAgents] = React.useState({});
  const [results, setResults] = React.useState([]);

  React.useEffect(() => {
    const url = `${BASE_URL.replace(/^http/, 'ws')}/self-healing/updates`;
    const ws = new WebSocket(url);
    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        if (data.gap !== undefined) {
          setGaps((g) => ({ ...g, [data.component]: data.gap }));
        }
        if (data.agent) {
          setAgents((a) => ({ ...a, [data.component || data.agent]: data.agent }));
        }
        if (data.result) {
          setResults((r) => [{ component: data.component, result: data.result }, ...r].slice(0, 10));
        }
      } catch (err) {
        console.error('self-healing panel', err);
      }
    };
    return () => ws.close();
  }, []);

  return React.createElement(
    'div',
    { id: 'self-healing-panel' },
    React.createElement('h3', null, 'Self Healing'),
    React.createElement(
      'div',
      { className: 'heartbeat-gaps' },
      Object.entries(gaps).map(([comp, gap]) =>
        React.createElement('div', { key: comp }, `${comp}: ${gap}`)
      )
    ),
    React.createElement(
      'div',
      { className: 'repair-agents' },
      Object.entries(agents).map(([comp, agent]) =>
        React.createElement('div', { key: comp }, `${comp}: ${agent}`)
      )
    ),
    React.createElement(
      'ul',
      { className: 'patch-results' },
      results.map((r, idx) =>
        React.createElement('li', { key: idx }, `${r.component}: ${r.result}`)
      )
    )
  );
}
