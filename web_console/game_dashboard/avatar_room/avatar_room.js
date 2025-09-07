import React from 'https://esm.sh/react@18';
import { BASE_URL } from '../../main.js';

function AvatarRoom() {
  const [phrase, setPhrase] = React.useState('');
  const [status, setStatus] = React.useState('');
  const [question, setQuestion] = React.useState('');
  const [answer, setAnswer] = React.useState('');

  const wave = () => fetch(`${BASE_URL}/avatar/wave`, { method: 'POST' });

  const speak = async () => {
    try {
      await fetch(`${BASE_URL}/avatar/speak`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phrase })
      });
      setPhrase('');
    } catch (err) {
      console.error('speak failed', err);
    }
  };

  const showStatus = async () => {
    try {
      const resp = await fetch(`${BASE_URL}/avatar/status`);
      setStatus(await resp.text());
    } catch (err) {
      setStatus('status error: ' + err);
    }
  };

  const askSidekick = async () => {
    try {
      const resp = await fetch(`${BASE_URL}/sidekick`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      });
      const data = await resp.json();
      setAnswer(data.answer);
      setQuestion('');
    } catch (err) {
      setAnswer('sidekick error: ' + err);
    }
  };

  return (
    React.createElement('div', {
      id: 'avatar-room',
      style: { display: 'flex', gap: '1rem', alignItems: 'flex-start' }
    },
      React.createElement('video', {
        id: 'avatar',
        width: 320,
        autoPlay: true,
        muted: true,
        playsInline: true
      }),
      React.createElement('div', null,
        React.createElement('div', { className: 'quick-commands' },
          React.createElement('input', {
            value: phrase,
            onChange: (e) => setPhrase(e.target.value),
            placeholder: 'Phrase...'
          }),
          React.createElement('button', { onClick: wave }, 'Wave'),
          React.createElement('button', { onClick: speak }, 'Speak'),
          React.createElement('button', { onClick: showStatus }, 'Status'),
          React.createElement('pre', null, status)
        ),
        React.createElement('div', { className: 'sidekick-chat', style: { marginTop: '1rem' } },
          React.createElement('input', {
            value: question,
            onChange: (e) => setQuestion(e.target.value),
            placeholder: 'Ask the sidekick...'
          }),
          React.createElement('button', { onClick: askSidekick }, 'Ask'),
          React.createElement('pre', null, answer)
        )
      )
    )
  );
}

export default AvatarRoom;
