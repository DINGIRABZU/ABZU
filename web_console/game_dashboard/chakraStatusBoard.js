import React from 'https://esm.sh/react@18';
import { BASE_URL } from '../main.js';

export default function ChakraStatusBoard() {
  const [data, setData] = React.useState({ status: 'unknown', heartbeats: {}, versions: {} });

  React.useEffect(() => {
    let timer;
    const poll = async () => {
      try {
        const resp = await fetch(`${BASE_URL}/chakra/status`);
        const json = await resp.json();
        setData({
          status: json.status,
          heartbeats: json.heartbeats || {},
          versions: json.versions || {}
        });
      } catch (err) {
        console.error('chakra board error', err);
      }
      timer = setTimeout(poll, 1000);
    };
    poll();
    return () => clearTimeout(timer);
  }, []);

  return React.createElement('div', { id: 'chakra-status-board' },
    React.createElement('h3', null, 'Chakra Status'),
    React.createElement('div', { className: 'chakra-rows' },
      Object.entries(data.heartbeats).map(([name, freq]) =>
        React.createElement('div', { key: name, className: 'chakra-row' },
          React.createElement('span', { className: 'chakra-name' }, name),
          React.createElement('span', { className: 'chakra-pulse' }, `${freq.toFixed(2)}Hz`),
          React.createElement('span', { className: 'chakra-state' }, data.status),
          React.createElement('span', { className: 'chakra-version' }, data.versions.state_validator || '')
        )
      )
    )
  );
}
