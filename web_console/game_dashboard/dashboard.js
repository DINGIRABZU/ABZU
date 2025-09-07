import React from 'https://esm.sh/react@18';
import { createRoot } from 'https://esm.sh/react-dom@18/client';
import { BASE_URL, startStream, connectEvents } from '../main.js';
import SetupWizard from './setupWizard.js';
import ChakraPulse from './chakraPulse.js';
import AvatarRoom from './avatarRoom.js';
import ChakraStatusBoard from './chakraStatusBoard.js';

function GameDashboard() {
  const buttons = [
    { id: 'ignite', label: 'Ignite', action: () => fetch(`${BASE_URL}/ignite`, { method: 'POST' }) },
    { id: 'memory', label: 'Memory Query', action: () => fetch(`${BASE_URL}/memory/query`, { method: 'POST' }) },
    { id: 'handover', label: 'Handover', action: () => fetch(`${BASE_URL}/handover`, { method: 'POST' }) }
  ];
  const [focusIndex, setFocusIndex] = React.useState(0);
  const [wizardDone, setWizardDone] = React.useState(() => localStorage.getItem('setupWizardCompleted') === 'true');

  React.useEffect(() => {
    if (wizardDone) {
      startStream();
      connectEvents();
    }
  }, [wizardDone]);

  React.useEffect(() => {
    if (!wizardDone) return;
    const btn = document.getElementById(buttons[focusIndex].id + '-btn');
    if (btn) btn.focus();
  }, [focusIndex, wizardDone]);

  React.useEffect(() => {
    if (!wizardDone) return;
    const handleKey = (e) => {
      if (e.key === 'ArrowRight') setFocusIndex((i) => (i + 1) % buttons.length);
      if (e.key === 'ArrowLeft') setFocusIndex((i) => (i + buttons.length - 1) % buttons.length);
      if (e.key === 'Enter' || e.key === ' ') buttons[focusIndex].action();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [focusIndex, wizardDone]);

  React.useEffect(() => {
    if (!wizardDone) return;
    let raf;
    const poll = () => {
      const [gp] = navigator.getGamepads ? navigator.getGamepads() : [];
      if (gp) {
        if (gp.buttons[14]?.pressed) setFocusIndex((i) => (i + buttons.length - 1) % buttons.length);
        if (gp.buttons[15]?.pressed) setFocusIndex((i) => (i + 1) % buttons.length);
        if (gp.buttons[0]?.pressed) buttons[focusIndex].action();
      }
      raf = requestAnimationFrame(poll);
    };
    window.addEventListener('gamepadconnected', () => poll());
    return () => cancelAnimationFrame(raf);
  }, [focusIndex, wizardDone]);

  if (!wizardDone) {
    return React.createElement(SetupWizard, { onComplete: () => setWizardDone(true) });
  }

  return (
    React.createElement('div', null,
      React.createElement('div', { className: 'mission-map' },
        buttons.map((btn) =>
          React.createElement('button', {
            id: btn.id + '-btn',
            key: btn.id,
            onClick: btn.action
          }, btn.label)
        )
      ),
      React.createElement(AvatarRoom, null),
      React.createElement('pre', { id: 'event-log', style: { marginTop: '1rem', textAlign: 'left' } }),
      React.createElement(ChakraPulse),
      React.createElement(ChakraStatusBoard)
    )
  );
}

const root = createRoot(document.getElementById('root'));
root.render(React.createElement(GameDashboard));
