import React from 'https://esm.sh/react@18';
import { createRoot } from 'https://esm.sh/react-dom@18/client';
import { BASE_URL, startStream, connectEvents } from '../main.js';
import SetupWizard from './setupWizard.js';
import MissionWizard from './missionWizard.js';
import ChakraPulse from './chakraPulse.js';
import AvatarRoom from './avatar_room/avatar_room.js';
import ChakraStatusBoard from './chakraStatusBoard.js';
import AgentStatusPanel from './agent_status_panel.js';
import ChatThreads from './chatThreads.js';
import MemoryPanel from './memory_panel/memory_panel.js';
import ChakraStatusPanel from './chakra_status_panel/chakra_status_panel.js';
import SelfHealingPanel from './self_healing_panel/self_healing_panel.js';
import ConnectorsPanel from './connectors_panel/connectors_panel.js';
import MissionMap from './mission_map.js';

const stageTitles = {
  'stage-a': 'Stage A – Alpha Automation',
  'stage-b': 'Stage B – Mission Ops',
  'stage-c': 'Stage C – Continuity Planning',
};

function GameDashboard() {
  const appendLog = React.useCallback((lines) => {
    const logEl = document.getElementById('event-log');
    if (!logEl) return;
    const entry = Array.isArray(lines) ? lines.join('\n') : String(lines ?? '');
    const text = entry.endsWith('\n') ? entry : `${entry}\n`;
    logEl.textContent += text;
    logEl.scrollTop = logEl.scrollHeight;
  }, []);

  const logLine = React.useCallback(
    (symbol, message) => {
      appendLog(`[${new Date().toISOString()}] ${symbol} ${message}`);
    },
    [appendLog]
  );

  const createLoggedAction = React.useCallback(
    (id, label, executor, { onError } = {}) => ({
      id,
      label,
      action: () => {
        logLine('▶', `${label} dispatched`);
        try {
          const result = executor();
          if (result && typeof result.then === 'function') {
            return result.catch((error) => {
              if (onError) {
                onError(error);
              } else {
                logLine('❌', `${label} failed: ${error?.message ?? error}`);
              }
              throw error;
            });
          }
          return result;
        } catch (error) {
          if (onError) {
            onError(error);
          } else {
            logLine('❌', `${label} failed: ${error?.message ?? error}`);
          }
          throw error;
        }
      },
    }),
    [logLine]
  );

  const formatStageABlock = React.useCallback((label, payload) => {
    const status = payload?.status === 'success' ? '✅' : '❌';
    const lines = [`[${new Date().toISOString()}] ${status} ${label}`];
    if (payload?.run_id) lines.push(`run: ${payload.run_id}`);
    if (payload?.log_dir) lines.push(`logs: ${payload.log_dir}`);
    if (payload?.stdout_path) lines.push(`stdout: ${payload.stdout_path}`);
    if (payload?.stderr_path) lines.push(`stderr: ${payload.stderr_path}`);
    if (payload?.summary) lines.push(`summary: ${payload.summary}`);
    if (payload?.summary_path) lines.push(`summary file: ${payload.summary_path}`);
    if (payload?.stdout_lines != null)
      lines.push(`stdout lines: ${payload.stdout_lines}`);
    if (payload?.stderr_lines != null)
      lines.push(`stderr lines: ${payload.stderr_lines}`);
    if (Array.isArray(payload?.stderr_tail) && payload.stderr_tail.length) {
      lines.push('stderr tail:');
      payload.stderr_tail.forEach((line) => lines.push(`  ${line}`));
    } else if (payload?.stderr) {
      lines.push(`stderr: ${payload.stderr}`);
    }
    if (payload?.error && !payload?.stderr_tail?.length) {
      lines.push(`error: ${payload.error}`);
    }
    return lines;
  }, []);

  const createStageAAction = React.useCallback(
    ({ id, label, endpoint }) =>
      createLoggedAction(
        id,
        label,
        () =>
          fetch(`${BASE_URL}${endpoint}`, { method: 'POST' })
            .then(async (response) => {
              const text = await response.text();
              let data = {};
              if (text) {
                try {
                  data = JSON.parse(text);
                } catch (err) {
                  data = {
                    status: 'error',
                    error: `Failed to parse response JSON: ${err}`,
                    raw: text,
                  };
                }
              }
              const payload = {
                status: response.ok ? 'success' : 'error',
                status_code: response.status,
                ...data,
              };
              appendLog(formatStageABlock(label, payload));
              if (!response.ok || payload.status === 'error') {
                const error = new Error(
                  payload.error ||
                    payload.detail ||
                    `${label} failed with status ${response.status}`
                );
                error.stageAResult = payload;
                throw error;
              }
              return payload;
            }),
        {
          onError: (error) => {
            if (error?.stageAResult) {
              return;
            }
            const payload = {
              status: 'error',
              error: error?.message ?? String(error),
            };
            appendLog(formatStageABlock(label, payload));
          },
        }
      ),
    [appendLog, createLoggedAction, formatStageABlock]
  );

  const logSuccess = React.useCallback(
    (label, detail) => {
      logLine('✅', `${label} ${detail}`);
    },
    [logLine]
  );

  const stages = React.useMemo(
    () => [
      {
        id: 'stage-a',
        title: stageTitles['stage-a'],
        actions: [
          createStageAAction({
            id: 'stage-a1-boot-telemetry',
            label: 'Stage A1 – Boot Telemetry',
            endpoint: '/alpha/stage-a1-boot-telemetry',
          }),
          createStageAAction({
            id: 'stage-a2-crown-replays',
            label: 'Stage A2 – Crown Replays',
            endpoint: '/alpha/stage-a2-crown-replays',
          }),
          createStageAAction({
            id: 'stage-a3-gate-shakeout',
            label: 'Stage A3 – Gate Shakeout',
            endpoint: '/alpha/stage-a3-gate-shakeout',
          }),
        ],
      },
      {
        id: 'stage-b',
        title: stageTitles['stage-b'],
        actions: [
          createLoggedAction('ignite', 'Ignite', () =>
            fetch(`${BASE_URL}/start_ignition`, { method: 'POST' })
              .then((r) => r.json())
              .then((d) => {
                logSuccess('Ignite', `status: ${d.status ?? 'acknowledged'}`);
                return d;
              })
          ),
          createLoggedAction('memory', 'Memory Query', () =>
            fetch(`${BASE_URL}/memory/query`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ query: 'demo' }),
            })
              .then((r) => r.json())
              .then((d) => {
                const count = Array.isArray(d?.results) ? d.results.length : 0;
                logSuccess('Memory Query', `returned ${count} result(s)`);
                return d;
              })
          ),
        ],
      },
      {
        id: 'stage-c',
        title: stageTitles['stage-c'],
        actions: [
          createLoggedAction('handover', 'Handover', () =>
            fetch(`${BASE_URL}/handover`, { method: 'POST' })
              .then((r) => r.json())
              .then((d) => {
                const target = d?.handover?.target ?? 'escalation queued';
                logSuccess('Handover', `response: ${target}`);
                return d;
              })
          ),
        ],
      },
    ],
    [createLoggedAction, createStageAAction, logSuccess]
  );
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
      React.createElement(MissionMap, { stages }),
      React.createElement(AvatarRoom, null),
      React.createElement('pre', { id: 'event-log', style: { marginTop: '1rem', textAlign: 'left' } }),
      React.createElement(ChakraPulse),
      React.createElement(ChakraStatusBoard),
      React.createElement(ChakraStatusPanel),
      React.createElement(AgentStatusPanel),
      React.createElement(ChatThreads),
      React.createElement(ConnectorsPanel),
      React.createElement(MemoryPanel),
      React.createElement(SelfHealingPanel)
    )
  );
}

const root = createRoot(document.getElementById('root'));
root.render(React.createElement(GameDashboard));
