import React from 'https://esm.sh/react@18';
import { BASE_URL } from '../main.js';

function AvatarRoom() {
  const [mode, setMode] = React.useState('2d');
  const [phrase, setPhrase] = React.useState('');
  const [status, setStatus] = React.useState('');
  const [avatar, setAvatar] = React.useState('default');
  const avatars = ['default', 'inanna', 'bana'];
  const missions = [
    { id: 'chakras', label: 'Teach me about the chakras' },
    { id: 'breathing', label: 'Guide a breathing exercise' }
  ];

  const selectAvatar = async (value) => {
    setAvatar(value);
    try {
      await fetch(`${BASE_URL}/avatar/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ avatar: value })
      });
    } catch (err) {
      console.error('select avatar failed', err);
    }
  };

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

  const runMission = (id) => {
    fetch(`${BASE_URL}/avatar/mission`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mission: id })
    });
  };

  return (
    React.createElement('div', { id: 'avatar-room' },
      React.createElement('div', { className: 'avatar-controls' },
        React.createElement('select', {
          value: avatar,
          onChange: (e) => selectAvatar(e.target.value)
        }, avatars.map((a) => React.createElement('option', { key: a, value: a }, a))),
        React.createElement('button', {
          onClick: () => setMode(mode === '2d' ? '3d' : '2d')
        }, `Switch to ${mode === '2d' ? '3D' : '2D'}`),
        React.createElement('button', { onClick: wave }, 'Wave'),
        React.createElement('input', {
          value: phrase,
          onChange: (e) => setPhrase(e.target.value),
          placeholder: 'Phrase...'
        }),
        React.createElement('button', { onClick: speak }, 'Speak'),
        React.createElement('button', { onClick: showStatus }, 'Show Status')
      ),
      React.createElement('pre', null, status),
      React.createElement('div', { className: 'mini-missions' },
        missions.map((m) => React.createElement('button', {
          key: m.id,
          onClick: () => runMission(m.id)
        }, m.label))
      ),
      React.createElement('video', {
        id: 'avatar',
        width: 320,
        autoPlay: true,
        muted: true,
        playsInline: true,
        style: mode === '3d' ? { transform: 'rotateY(20deg)' } : {}
      })
    )
  );
}

export default AvatarRoom;
