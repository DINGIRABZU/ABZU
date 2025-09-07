import React from 'https://esm.sh/react@18';
import { BASE_URL } from '../main.js';

export default function AgentStatusPanel({ initialData }) {
  const [agents, setAgents] = React.useState(initialData || {});

  React.useEffect(() => {
    if (initialData) return; // skip polling when injected data supplied
    let timer;
    const poll = async () => {
      try {
        const resp = await fetch(`${BASE_URL}/agents/status`);
        const json = await resp.json();
        setAgents(json.agents || {});
      } catch (err) {
        console.error('agent status error', err);
      }
      timer = setTimeout(poll, 1000);
    };
    poll();
    return () => clearTimeout(timer);
  }, [initialData]);

  return React.createElement(
    'div',
    { id: 'agent-status-panel' },
    React.createElement('h3', null, 'Agent Status'),
    React.createElement(
      'div',
      { className: 'agent-rows' },
      Object.entries(agents).map(([name, info]) =>
        React.createElement(
          'div',
          { key: name, className: 'agent-row' },
          React.createElement('span', { className: 'agent-name' }, name),
          React.createElement('span', { className: 'agent-action' }, info.last_action || ''),
          React.createElement('span', { className: 'agent-chakra' }, info.chakra || ''),
          React.createElement(
            'span',
            { className: 'agent-heartbeat' },
            info.last_beat ? new Date(info.last_beat * 1000).toISOString() : ''
          )
        )
      )
    )
  );
}
