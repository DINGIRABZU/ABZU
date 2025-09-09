import React from 'https://esm.sh/react@18';
import { createRoot } from 'https://esm.sh/react-dom@18/client';
import { BASE_URL, startStream, connectEvents } from '../main.js';
import SetupWizard from './setupWizard.js';
import MissionWizard from './missionWizard.js';
import ChakraPulse from './chakraPulse.js';
import AvatarRoom from './avatar_room/avatar_room.js';
import ChakraStatusBoard from './chakraStatusBoard.js';
import AgentStatusPanel from './agent_status_panel.js';
import MemoryPanel from './memory_panel/memory_panel.js';
import ChakraStatusPanel from './chakra_status_panel/chakra_status_panel.js';
import SelfHealingPanel from './self_healing_panel/self_healing_panel.js';
import ConnectorsPanel from './connectors_panel/connectors_panel.js';
import MissionMap from './mission_map.js';

function GameDashboard() {
  const buttons = [
    {
      id: 'ignite',
      label: 'Ignite',
      action: () =>
        fetch(`${BASE_URL}/start_ignition`, { method: 'POST' })
          .then((r) => r.json())
          .then((d) => console.log(d)),
    },
    {
      id: 'memory',
      label: 'Memory Query',
      action: () =>
        fetch(`${BASE_URL}/memory/query`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: 'demo' }),
        })
          .then((r) => r.json())
          .then((d) => console.log(d)),
    },
    {
      id: 'handover',
      label: 'Handover',
      action: () =>
        fetch(`${BASE_URL}/handover`, { method: 'POST' })
          .then((r) => r.json())
          .then((d) => console.log(d)),
    },
  ];
  const [wizardDone, setWizardDone] = React.useState(() => localStorage.getItem('setupWizardCompleted') === 'true');
  const [missionDone, setMissionDone] = React.useState(() => localStorage.getItem('missionWizardCompleted') === 'true');

  React.useEffect(() => {
    if (wizardDone && missionDone) {
      startStream();
      connectEvents();
    }
  }, [wizardDone, missionDone]);


  if (!wizardDone) {
    return React.createElement(SetupWizard, { onComplete: () => setWizardDone(true) });
  }
  if (!missionDone) {
    return React.createElement(MissionWizard, { onComplete: () => setMissionDone(true) });
  }

  return (
    React.createElement('div', null,
      React.createElement(MissionMap, { buttons }),
      React.createElement(AvatarRoom, null),
      React.createElement('pre', { id: 'event-log', style: { marginTop: '1rem', textAlign: 'left' } }),
      React.createElement(ChakraPulse),
      React.createElement(ChakraStatusBoard),
      React.createElement(ChakraStatusPanel),
      React.createElement(AgentStatusPanel),
      React.createElement(ConnectorsPanel),
      React.createElement(MemoryPanel),
      React.createElement(SelfHealingPanel)
    )
  );
}

const root = createRoot(document.getElementById('root'));
root.render(React.createElement(GameDashboard));
