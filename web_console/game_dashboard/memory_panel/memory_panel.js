import React from 'https://esm.sh/react@18';
import { BASE_URL } from '../main.js';

export default function MemoryPanel() {
  const [metrics, setMetrics] = React.useState({ chakras: {} });
  const [query, setQuery] = React.useState('');
  const [results, setResults] = React.useState([]);
  const [chakra, setChakra] = React.useState('');
  const [purged, setPurged] = React.useState('');

  async function load() {
    try {
      const resp = await fetch(`${BASE_URL}/memory/query`, {
        headers: { 'x-api-key': 'test' }
      });
      const json = await resp.json();
      setMetrics(json);
    } catch (err) {
      console.error('memory metrics error', err);
    }
  }

  React.useEffect(() => {
    load();
  }, []);

  async function search(e) {
    e.preventDefault();
    try {
      const resp = await fetch(
        `${BASE_URL}/memory/query?q=${encodeURIComponent(query)}`,
        { headers: { 'x-api-key': 'test' } }
      );
      const json = await resp.json();
      setResults(json.results || []);
    } catch (err) {
      console.error('memory search error', err);
    }
  }

  async function purge(e) {
    e.preventDefault();
    try {
      const resp = await fetch(
        `${BASE_URL}/memory/purge?chakra=${encodeURIComponent(chakra)}`,
        {
          method: 'POST',
          headers: { 'x-api-key': 'test' }
        }
      );
      const json = await resp.json();
      setPurged(json.purged || '');
      await load();
    } catch (err) {
      console.error('memory purge error', err);
    }
  }

  return React.createElement('div', { id: 'memory-panel' },
    React.createElement('h3', null, 'Memory'),
    React.createElement('div', { className: 'chakra-rows' },
      Object.entries(metrics.chakras || {}).map(([name, info]) =>
        React.createElement('div', { key: name, className: 'chakra-row' },
          React.createElement('span', { className: 'chakra-name' }, name),
          React.createElement('span', { className: 'memory-count' }, info.count || 0),
          React.createElement('span', { className: 'last-heartbeat' }, info.last_heartbeat || 'n/a')
        )
      )
    ),
    React.createElement('form', { onSubmit: search },
      React.createElement('input', {
        value: query,
        onChange: (e) => setQuery(e.target.value)
      }),
      React.createElement('button', { type: 'submit' }, 'Search')
    ),
    React.createElement('ul', null,
      results.map((r, i) => React.createElement('li', { key: i }, r))
    ),
    React.createElement('form', { onSubmit: purge },
      React.createElement('input', {
        value: chakra,
        onChange: (e) => setChakra(e.target.value),
        placeholder: 'chakra'
      }),
      React.createElement('button', { type: 'submit' }, 'Purge'),
      purged && React.createElement('span', { className: 'purge-result' }, ` Purged ${purged}`)
    )
  );
}
