import React from 'https://esm.sh/react@18';
import { BASE_URL } from '../main.js';

export default function ChatThreads() {
  const [threads, setThreads] = React.useState([]);

  React.useEffect(() => {
    fetch(`${BASE_URL}/agent/chat/threads`)
      .then((r) => r.json())
      .then((d) => setThreads(d.threads || []))
      .catch(() => setThreads([]));
  }, []);

  return React.createElement(
    'ul',
    { id: 'chat-threads' },
    threads.map((t, i) => React.createElement('li', { key: i }, t))
  );
}
