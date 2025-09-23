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
    if (payload?.metrics) {
      lines.push('metrics:');
      try {
        const metricsLines = JSON.stringify(payload.metrics, null, 2).split('\n');
        metricsLines.forEach((line) => lines.push(`  ${line}`));
      } catch (err) {
        lines.push(`  [metrics JSON failed: ${err?.message ?? err}]`);
      }
    }
    if (payload?.metrics_error) {
      lines.push(`metrics error: ${payload.metrics_error}`);
    }
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

  const [stageBResults, setStageBResults] = React.useState({});

  const logStreamChunk = React.useCallback(
    (label, chunk) => {
      if (!chunk) return;
      chunk
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean)
        .forEach((line) => {
          appendLog(`[${new Date().toISOString()}] 📡 ${label}: ${line}`);
        });
    },
    [appendLog]
  );

  const streamJsonPost = React.useCallback(
    async (endpoint, label) => {
      const response = await fetch(`${BASE_URL}${endpoint}`, { method: 'POST' });
      let raw = '';
      if (response.body && response.body.getReader) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        while (true) {
          const { value, done } = await reader.read();
          if (done) {
            raw += decoder.decode();
            break;
          }
          const chunk = decoder.decode(value, { stream: true });
          raw += chunk;
          logStreamChunk(label, chunk);
        }
      } else {
        raw = await response.text();
        logStreamChunk(label, raw);
      }
      let data = null;
      let parseError = null;
      if (raw.trim()) {
        try {
          data = JSON.parse(raw);
        } catch (err) {
          parseError = err;
        }
      }
      return { response, data, raw, parseError };
    },
    [logStreamChunk]
  );

  const renderStageBDetails = React.useCallback(
    (id) => {
      const entry = stageBResults[id];
      if (!entry) return null;
      const elements = [];
      elements.push(
        React.createElement(
          'p',
          { key: 'status', className: `mission-stage__status mission-stage__status--${entry.status}` },
          `Status: ${entry.status}`
        )
      );
      if (entry.responseStatus != null) {
        elements.push(
          React.createElement(
            'p',
            { key: 'http' },
            `HTTP status: ${entry.responseStatus}`
          )
        );
      }
      if (entry.runId) {
        elements.push(
          React.createElement('p', { key: 'run' }, `Run ID: ${entry.runId}`)
        );
      }
      if (entry.logDir) {
        elements.push(
          React.createElement('p', { key: 'logs' }, `Log dir: ${entry.logDir}`)
        );
      }
      if (entry.summaryPath) {
        elements.push(
          React.createElement(
            'p',
            { key: 'summary-path' },
            `Summary: ${entry.summaryPath}`
          )
        );
      }
      if (entry.stdoutPath) {
        elements.push(
          React.createElement(
            'p',
            { key: 'stdout-path' },
            `Stdout: ${entry.stdoutPath}`
          )
        );
      }
      if (entry.stderrPath) {
        elements.push(
          React.createElement(
            'p',
            { key: 'stderr-path' },
            `Stderr: ${entry.stderrPath}`
          )
        );
      }
      if (entry.startedAt) {
        elements.push(
          React.createElement(
            'p',
            { key: 'started' },
            `Started: ${entry.startedAt}`
          )
        );
      }
      if (entry.completedAt) {
        elements.push(
          React.createElement(
            'p',
            { key: 'completed' },
            `Completed: ${entry.completedAt}`
          )
        );
      }
      if (entry.error) {
        elements.push(
          React.createElement(
            'p',
            { key: 'error', className: 'mission-stage__error' },
            `Error: ${entry.error}`
          )
        );
      }
      if (entry.metricsError) {
        elements.push(
          React.createElement(
            'p',
            { key: 'metrics-error', className: 'mission-stage__error' },
            `Metrics error: ${entry.metricsError}`
          )
        );
      }
      if (entry.metrics) {
        elements.push(
          React.createElement(
            'pre',
            { key: 'metrics', className: 'mission-stage__metrics' },
            JSON.stringify(entry.metrics, null, 2)
          )
        );
      }
      if (entry.rawResponse && !entry.metrics) {
        elements.push(
          React.createElement(
            'pre',
            { key: 'raw', className: 'mission-stage__metrics' },
            entry.rawResponse
          )
        );
      }
      return React.createElement(
        'div',
        { className: 'mission-stage__details', key: `${id}-details` },
        elements
      );
    },
    [stageBResults]
  );

  const createStageBAction = React.useCallback(
    ({ id, label, endpoint }) => {
      const execute = async () => {
        const startedAt = new Date().toISOString();
        setStageBResults((prev) => ({
          ...prev,
          [id]: {
            status: 'running',
            startedAt,
            completedAt: null,
            error: null,
            metrics: null,
            metricsError: null,
            runId: null,
            logDir: null,
            summaryPath: null,
            stdoutPath: null,
            stderrPath: null,
            responseStatus: null,
            rawResponse: null,
          },
        }));
        const { response, data, raw, parseError } = await streamJsonPost(
          endpoint,
          label
        );
        if (parseError) {
          const message = `Failed to parse response JSON: ${parseError.message}`;
          const completedAt = new Date().toISOString();
          setStageBResults((prev) => ({
            ...prev,
            [id]: {
              ...(prev[id] ?? {}),
              status: 'error',
              startedAt,
              completedAt,
              error: message,
              metrics: null,
              metricsError: null,
              responseStatus: response?.status ?? null,
              rawResponse: raw,
            },
          }));
          throw new Error(message);
        }
        const payload = {
          status: response.ok ? 'success' : 'error',
          status_code: response.status,
          ...(data ?? {}),
        };
        appendLog(formatStageABlock(label, payload));
        const completedAt = new Date().toISOString();
        const baseUpdate = {
          status: payload.status,
          startedAt,
          completedAt,
          error: null,
          metrics: payload.metrics ?? null,
          metricsError: payload.metrics_error ?? null,
          runId: payload.run_id ?? null,
          logDir: payload.log_dir ?? null,
          summaryPath: payload.summary_path ?? null,
          stdoutPath: payload.stdout_path ?? null,
          stderrPath: payload.stderr_path ?? null,
          responseStatus: response.status,
          rawResponse: raw,
        };
        if (payload.status !== 'success') {
          baseUpdate.error =
            payload.error || payload.detail || payload.metrics_error ||
            `HTTP ${response.status}`;
          setStageBResults((prev) => ({ ...prev, [id]: baseUpdate }));
          const error = new Error(baseUpdate.error);
          error.stageResult = payload;
          throw error;
        }
        if (payload.metrics_error) {
          baseUpdate.error = payload.metrics_error;
          baseUpdate.status = 'error';
          setStageBResults((prev) => ({ ...prev, [id]: baseUpdate }));
          const error = new Error(payload.metrics_error);
          error.stageResult = payload;
          throw error;
        }
        setStageBResults((prev) => ({ ...prev, [id]: baseUpdate }));
        return payload;
      };

      const action = createLoggedAction(id, label, execute, {
        onError: (error) => {
          if (error?.stageResult) {
            return;
          }
          setStageBResults((prev) => ({
            ...prev,
            [id]: {
              ...(prev[id] ?? {}),
              status: 'error',
              error: error?.message ?? String(error),
              completedAt: new Date().toISOString(),
            },
          }));
        },
      });

      return {
        ...action,
        renderDetails: () => renderStageBDetails(id),
      };
    },
    [createLoggedAction, formatStageABlock, renderStageBDetails, streamJsonPost, appendLog]
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
          createStageBAction({
            id: 'stage-b1-memory-proof',
            label: 'Stage B1 – Memory Proof',
            endpoint: '/alpha/stage-b1-memory-proof',
          }),
          createStageBAction({
            id: 'stage-b2-sonic-rehearsal',
            label: 'Stage B2 – Sonic Rehearsal',
            endpoint: '/alpha/stage-b2-sonic-rehearsal',
          }),
          createStageBAction({
            id: 'stage-b3-connector-rotation',
            label: 'Stage B3 – Connector Rotation',
            endpoint: '/alpha/stage-b3-connector-rotation',
          }),
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
    [createLoggedAction, createStageAAction, createStageBAction, logSuccess]
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
