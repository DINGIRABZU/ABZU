import React from 'https://esm.sh/react@18';
import { BASE_URL } from '../main.js';

export default function SelfHealingPanel({ initialLedger, initialActive }) {
  const [ledger, setLedger] = React.useState(initialLedger || []);
  const [active, setActive] = React.useState(initialActive || {});

  React.useEffect(() => {
    if (initialLedger || typeof fetch === 'undefined') return;
    (async () => {
      try {
        const resp = await fetch(`${BASE_URL}/self-healing/ledger`);
        const json = await resp.json();
        setLedger(json.ledger || []);
        setActive(json.active || {});
      } catch (err) {
        console.error('self-healing ledger', err);
      }
    })();
  }, [initialLedger]);

  React.useEffect(() => {
    const url = `${BASE_URL.replace(/^http/, 'ws')}/self-healing/updates`;
    const ws = new WebSocket(url);
    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        setLedger((l) => [data, ...l].slice(0, 50));
        if (data.event === 'final_status') {
          setActive((a) => {
            const n = { ...a };
            delete n[data.component];
            return n;
          });
        } else if (data.event && data.component) {
          setActive((a) => ({ ...a, [data.component]: data.timestamp }));
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
      { className: 'active-repairs' },
      Object.entries(active).map(([comp, ts]) =>
        React.createElement('div', { key: comp }, `${comp}: ${new Date(ts * 1000).toISOString()}`)
      )
    ),
    React.createElement(
      'ul',
      { className: 'ledger-events' },
      ledger.map((e, idx) =>
        React.createElement('li', { key: idx }, `${e.event}: ${e.component}`)
      )
    )
  );
}
