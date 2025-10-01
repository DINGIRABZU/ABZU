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
  'stage-d': 'Stage D – Neo-APSU Bridge',
};

const stageAFallback = {
  'stage-a1-boot-telemetry': {
    status: 'error',
    runId: '20250924T115244Z-stage_a1_boot_telemetry',
    logDir: 'logs/stage_a/20250924T115244Z-stage_a1_boot_telemetry',
    summaryPath: 'logs/stage_a/20250924T115244Z-stage_a1_boot_telemetry/summary.json',
    stdoutPath:
      'logs/stage_a/20250924T115244Z-stage_a1_boot_telemetry/stage_a1_boot_telemetry.stdout.log',
    stderrPath:
      'logs/stage_a/20250924T115244Z-stage_a1_boot_telemetry/stage_a1_boot_telemetry.stderr.log',
    error: 'stage_a1_boot_telemetry exited with code 1',
    notes:
      'environment-limited: Stage runtime shim missing—env_validation not on sys.path inside Codex sandbox.',
  },
  'stage-a2-crown-replays': {
    status: 'error',
    runId: '20250924T115245Z-stage_a2_crown_replays',
    logDir: 'logs/stage_a/20250924T115245Z-stage_a2_crown_replays',
    summaryPath: 'logs/stage_a/20250924T115245Z-stage_a2_crown_replays/summary.json',
    stdoutPath:
      'logs/stage_a/20250924T115245Z-stage_a2_crown_replays/stage_a2_crown_replays.stdout.log',
    stderrPath:
      'logs/stage_a/20250924T115245Z-stage_a2_crown_replays/stage_a2_crown_replays.stderr.log',
    error: 'stage_a2_crown_replays exited with code 1',
    notes:
      'environment-limited: Stage runtime shim missing—Crown modules not importable from sandbox working directory.',
  },
  'stage-a3-gate-shakeout': {
    status: 'error',
    runId: '20250924T115245Z-stage_a3_gate_shakeout',
    logDir: 'logs/stage_a/20250924T115245Z-stage_a3_gate_shakeout',
    summaryPath: 'logs/stage_a/20250924T115245Z-stage_a3_gate_shakeout/summary.json',
    stdoutPath:
      'logs/stage_a/20250924T115245Z-stage_a3_gate_shakeout/stage_a3_gate_shakeout.stdout.log',
    stderrPath:
      'logs/stage_a/20250924T115245Z-stage_a3_gate_shakeout/stage_a3_gate_shakeout.stderr.log',
    error: 'stage_a3_gate_shakeout exited with code 1',
    notes: 'Gate shakeout logged completion but exited non-zero for follow-up triage.',
  },
};

const stageBFallback = {
  'stage-b1-memory-proof': {
    status: 'error',
    runId: '20250924T115245Z-stage_b1_memory_proof',
    logDir: 'logs/stage_b/20250924T115245Z-stage_b1_memory_proof',
    summaryPath: 'logs/stage_b/20250924T115245Z-stage_b1_memory_proof/summary.json',
    stdoutPath:
      'logs/stage_b/20250924T115245Z-stage_b1_memory_proof/stage_b1_memory_proof.stdout.log',
    stderrPath:
      'logs/stage_b/20250924T115245Z-stage_b1_memory_proof/stage_b1_memory_proof.stderr.log',
    error: 'stage_b1_memory_proof exited with code 1',
    metricsError: 'no JSON payload found in command stdout',
    notes: "Rust neoabzu_memory bindings missing; load proof can't initialise bundle.",
  },
  'stage-b2-sonic-rehearsal': {
    status: 'success',
    runId: '20250924T115254Z-stage_b2_sonic_rehearsal',
    logDir: 'logs/stage_b/20250924T115254Z-stage_b2_sonic_rehearsal',
    summaryPath: 'logs/stage_b/20250924T115254Z-stage_b2_sonic_rehearsal/summary.json',
    stdoutPath:
      'logs/stage_b/20250924T115254Z-stage_b2_sonic_rehearsal/stage_b2_sonic_rehearsal.stdout.log',
    stderrPath:
      'logs/stage_b/20250924T115254Z-stage_b2_sonic_rehearsal/stage_b2_sonic_rehearsal.stderr.log',
    notes: 'Rehearsal packet exported to stage_b_rehearsal_packet.json.',
  },
  'stage-b3-connector-rotation': {
    status: 'error',
    runId: '20250924T115254Z-stage_b3_connector_rotation',
    logDir: 'logs/stage_b/20250924T115254Z-stage_b3_connector_rotation',
    summaryPath: 'logs/stage_b/20250924T115254Z-stage_b3_connector_rotation/summary.json',
    stdoutPath:
      'logs/stage_b/20250924T115254Z-stage_b3_connector_rotation/stage_b3_connector_rotation.stdout.log',
    stderrPath:
      'logs/stage_b/20250924T115254Z-stage_b3_connector_rotation/stage_b3_connector_rotation.stderr.log',
    error: 'stage_b3_connector_rotation exited with code 1',
    metricsError: 'no JSON payload found in command stdout',
    notes: 'Connector rehearsal blocked: connectors package import failed inside smoke script.',
  },
};

const stageDFallback = {
  'stage-d1-neoapsu-memory': {
    status: 'error',
    runId: '20250930T120000Z-stage_d1_neoapsu_memory',
    logDir: 'logs/stage_d/neoapsu_memory/20250930T120000Z-stage_d1_neoapsu_memory',
    summaryPath:
      'logs/stage_d/neoapsu_memory/20250930T120000Z-stage_d1_neoapsu_memory/summary.json',
    stdoutPath:
      'logs/stage_d/neoapsu_memory/20250930T120000Z-stage_d1_neoapsu_memory/stage_d1_neoapsu_memory.stdout.log',
    stderrPath:
      'logs/stage_d/neoapsu_memory/20250930T120000Z-stage_d1_neoapsu_memory/stage_d1_neoapsu_memory.stderr.log',
    error: 'stage_d1_neoapsu_memory exited with code 1',
    notes:
      'Sandbox stub engaged; install neoapsu_memory bindings to clear stubbed warnings.',
  },
  'stage-d2-neoapsu-crown': {
    status: 'error',
    runId: '20250930T120000Z-stage_d2_neoapsu_crown',
    logDir: 'logs/stage_d/neoapsu_crown/20250930T120000Z-stage_d2_neoapsu_crown',
    summaryPath:
      'logs/stage_d/neoapsu_crown/20250930T120000Z-stage_d2_neoapsu_crown/summary.json',
    stdoutPath:
      'logs/stage_d/neoapsu_crown/20250930T120000Z-stage_d2_neoapsu_crown/stage_d2_neoapsu_crown.stdout.log',
    stderrPath:
      'logs/stage_d/neoapsu_crown/20250930T120000Z-stage_d2_neoapsu_crown/stage_d2_neoapsu_crown.stderr.log',
    error: 'stage_d2_neoapsu_crown exited with code 1',
    notes:
      'Neo-APSU crown contracts deferred – sandbox summary archived for readiness bundle.',
  },
  'stage-d3-neoapsu-identity': {
    status: 'error',
    runId: '20250930T120000Z-stage_d3_neoapsu_identity',
    logDir: 'logs/stage_d/neoapsu_identity/20250930T120000Z-stage_d3_neoapsu_identity',
    summaryPath:
      'logs/stage_d/neoapsu_identity/20250930T120000Z-stage_d3_neoapsu_identity/summary.json',
    stdoutPath:
      'logs/stage_d/neoapsu_identity/20250930T120000Z-stage_d3_neoapsu_identity/stage_d3_neoapsu_identity.stdout.log',
    stderrPath:
      'logs/stage_d/neoapsu_identity/20250930T120000Z-stage_d3_neoapsu_identity/stage_d3_neoapsu_identity.stderr.log',
    error: 'stage_d3_neoapsu_identity exited with code 1',
    notes:
      'Identity bridge verification stubbed – sync native crate to replace sandbox report.',
  },
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
    if (payload?.artifacts && typeof payload.artifacts === 'object') {
      lines.push('artifacts:');
      Object.entries(payload.artifacts).forEach(([key, value]) => {
        lines.push(`  ${key}: ${value}`);
      });
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
    if (payload?.raw) {
      lines.push(`raw: ${payload.raw}`);
    }
    if (payload?.error && !payload?.stderr_tail?.length) {
      lines.push(`error: ${payload.error}`);
    }
    return lines;
  }, []);

  const [stageAResults, setStageAResults] = React.useState(() => ({
    ...stageAFallback,
  }));
  const renderStageADetails = React.useCallback(
    (id) => {
      const entry = stageAResults[id] ?? stageAFallback[id];
      if (!entry) return null;
      const elements = [];
      if (entry.status) {
        elements.push(
          React.createElement(
            'p',
            {
              key: 'status',
              className: `mission-stage__status mission-stage__status--${entry.status}`,
            },
            `Status: ${entry.status}`
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
          React.createElement('p', { key: 'started' }, `Started: ${entry.startedAt}`)
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
      if (entry.notes) {
        elements.push(
          React.createElement('p', { key: 'notes' }, `Notes: ${entry.notes}`)
        );
      }
      if (entry.artifacts && Object.keys(entry.artifacts).length) {
        elements.push(
          React.createElement(
            'div',
            { key: 'artifacts' },
            [
              React.createElement('p', { key: 'artifacts-label' }, 'Artifacts:'),
              React.createElement(
                'ul',
                { key: 'artifacts-list' },
                Object.entries(entry.artifacts).map(([key, value]) =>
                  React.createElement('li', { key }, `${key}: ${value}`)
                )
              ),
            ]
          )
        );
      }
      return React.createElement(
        'div',
        { className: 'mission-stage__details', key: `${id}-details` },
        elements
      );
    },
    [stageAResults]
  );

  const createStageAAction = React.useCallback(
    ({ id, label, endpoint }) => {
      const execute = () => {
        const startedAt = new Date().toISOString();
        setStageAResults((prev) => ({
          ...prev,
          [id]: {
            ...(prev[id] ?? stageAFallback[id] ?? {}),
            status: 'running',
            startedAt,
            completedAt: null,
            error: null,
            responseStatus: null,
            artifacts: null,
          },
        }));
        return fetch(`${BASE_URL}${endpoint}`, { method: 'POST' })
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
            const fallback = stageAFallback[id] ?? {};
            const completedAt = new Date().toISOString();
            const baseUpdate = {
              status: payload.status,
              startedAt,
              completedAt,
              runId: payload.run_id ?? fallback.runId ?? null,
              logDir: payload.log_dir ?? fallback.logDir ?? null,
              summaryPath: payload.summary_path ?? fallback.summaryPath ?? null,
              stdoutPath: payload.stdout_path ?? fallback.stdoutPath ?? null,
              stderrPath: payload.stderr_path ?? fallback.stderrPath ?? null,
              responseStatus: response.status,
              error: payload.error || payload.detail || null,
              notes: fallback.notes ?? null,
              artifacts: payload.artifacts ?? fallback.artifacts ?? null,
            };
            setStageAResults((prev) => ({ ...prev, [id]: baseUpdate }));
            if (!response.ok || payload.status === 'error') {
              const error = new Error(
                baseUpdate.error || `${label} failed with status ${response.status}`
              );
              error.stageAResult = payload;
              throw error;
            }
            return payload;
          })
          .catch((error) => {
            const fallback = stageAFallback[id] ?? {};
            setStageAResults((prev) => ({
              ...prev,
              [id]: {
                ...(prev[id] ?? fallback),
                status: 'error',
                completedAt: new Date().toISOString(),
                error:
                  error?.stageAResult?.error ||
                  error?.stageAResult?.detail ||
                  error?.message ||
                  String(error),
                notes: fallback.notes ?? null,
                artifacts: fallback.artifacts ?? null,
              },
            }));
            throw error;
          });
      };

      const action = createLoggedAction(id, label, execute, {
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
      });

      return {
        ...action,
        status: stageAResults[id]?.status ?? stageAFallback[id]?.status ?? null,
        renderDetails: () => renderStageADetails(id),
      };
    },
    [
      appendLog,
      createLoggedAction,
      formatStageABlock,
      renderStageADetails,
      stageAResults,
    ]
  );

  const [stageBResults, setStageBResults] = React.useState(() => ({
    ...stageBFallback,
  }));
  const [stageCResults, setStageCResults] = React.useState({});
  const [stageDResults, setStageDResults] = React.useState(() => ({
    ...stageDFallback,
  }));

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
      const entry = stageBResults[id] ?? stageBFallback[id];
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
      if (entry.notes) {
        elements.push(
          React.createElement('p', { key: 'notes' }, `Notes: ${entry.notes}`)
        );
      }
      if (entry.artifacts && Object.keys(entry.artifacts).length) {
        elements.push(
          React.createElement(
            'div',
            { key: 'artifacts' },
            [
              React.createElement('p', { key: 'artifacts-label' }, 'Artifacts:'),
              React.createElement(
                'ul',
                { key: 'artifacts-list' },
                Object.entries(entry.artifacts).map(([key, value]) =>
                  React.createElement('li', { key }, `${key}: ${value}`)
                )
              ),
            ]
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
            ...(prev[id] ?? stageBFallback[id] ?? {}),
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
            stderrTail: null,
            artifacts: null,
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
              ...(prev[id] ?? stageBFallback[id] ?? {}),
              status: 'error',
              startedAt,
              completedAt,
              error: message,
              metrics: null,
              metricsError: null,
              responseStatus: response?.status ?? null,
              rawResponse: raw,
              stderrTail: null,
              artifacts:
                (prev[id] ?? stageBFallback[id] ?? {}).artifacts ?? null,
            },
          }));
          appendLog(
            formatStageABlock(label, {
              status: 'error',
              error: message,
              raw,
            })
          );
          throw new Error(message);
        }
        const payload = {
          status: response.ok ? 'success' : 'error',
          status_code: response.status,
          ...(data ?? {}),
        };
        appendLog(formatStageABlock(label, payload));
        const completedAt = new Date().toISOString();
        const fallback = stageBFallback[id] ?? {};
        const baseUpdate = {
          status: payload.status,
          startedAt,
          completedAt,
          error: null,
          metrics: payload.metrics ?? null,
          metricsError: payload.metrics_error ?? null,
          runId: payload.run_id ?? null,
          logDir: payload.log_dir ?? fallback.logDir ?? null,
          summaryPath: payload.summary_path ?? fallback.summaryPath ?? null,
          stdoutPath: payload.stdout_path ?? fallback.stdoutPath ?? null,
          stderrPath: payload.stderr_path ?? fallback.stderrPath ?? null,
          responseStatus: response.status,
          rawResponse: raw,
          notes: fallback.notes ?? null,
          stderrTail: payload.stderr_tail ?? null,
          artifacts: payload.artifacts ?? fallback.artifacts ?? null,
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
              ...(prev[id] ?? stageBFallback[id] ?? {}),
              status: 'error',
              error: error?.message ?? String(error),
              completedAt: new Date().toISOString(),
              artifacts:
                (prev[id] ?? stageBFallback[id] ?? {}).artifacts ?? null,
            },
          }));
          appendLog(
            formatStageABlock(label, {
              status: 'error',
              error: error?.message ?? String(error),
            })
          );
        },
      });

      return {
        ...action,
        status: stageBResults[id]?.status ?? stageBFallback[id]?.status ?? null,
        renderDetails: () => renderStageBDetails(id),
      };
    },
    [
      createLoggedAction,
      formatStageABlock,
      renderStageBDetails,
      streamJsonPost,
      appendLog,
      stageBResults,
    ]
  );

  const renderStageCDetails = React.useCallback(
    (id) => {
      const entry = stageCResults[id];
      if (!entry) return null;
      const elements = [];
      if (entry.status) {
        elements.push(
          React.createElement(
            'p',
            {
              key: 'status',
              className: `mission-stage__status mission-stage__status--${entry.status}`,
            },
            `Status: ${entry.status}`
          )
        );
      }
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
          React.createElement('p', { key: 'summary' }, `Summary: ${entry.summaryPath}`)
        );
      }
      if (entry.stdoutPath) {
        elements.push(
          React.createElement('p', { key: 'stdout' }, `Stdout: ${entry.stdoutPath}`)
        );
      }
      if (entry.stderrPath) {
        elements.push(
          React.createElement('p', { key: 'stderr' }, `Stderr: ${entry.stderrPath}`)
        );
      }
      if (entry.startedAt) {
        elements.push(
          React.createElement('p', { key: 'started' }, `Started: ${entry.startedAt}`)
        );
      }
      if (entry.completedAt) {
        elements.push(
          React.createElement('p', { key: 'completed' }, `Completed: ${entry.completedAt}`)
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
      if (entry.artifacts && Object.keys(entry.artifacts).length) {
        elements.push(
          React.createElement(
            'div',
            { key: 'artifacts' },
            [
              React.createElement('p', { key: 'artifacts-label' }, 'Artifacts:'),
              React.createElement(
                'ul',
                { key: 'artifacts-list' },
                Object.entries(entry.artifacts).map(([key, value]) =>
                  React.createElement('li', { key }, `${key}: ${value}`)
                )
              ),
            ]
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
      if (entry.stderrTail && entry.stderrTail.length) {
        elements.push(
          React.createElement(
            'pre',
            { key: 'stderr-tail', className: 'mission-stage__metrics' },
            entry.stderrTail.join('\n')
          )
        );
      } else if (entry.stderr) {
        elements.push(
          React.createElement(
            'pre',
            { key: 'stderr-text', className: 'mission-stage__metrics' },
            entry.stderr
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
      if (!elements.length) {
        return null;
      }
      return React.createElement(
        'div',
        { className: 'mission-stage__details', key: `${id}-details` },
        elements
      );
    },
    [stageCResults]
  );

  const renderStageDDetails = React.useCallback(
    (id) => {
      const entry = stageDResults[id] ?? stageDFallback[id];
      if (!entry) return null;
      const elements = [];
      if (entry.status) {
        elements.push(
          React.createElement(
            'p',
            {
              key: 'status',
              className: `mission-stage__status mission-stage__status--${entry.status}`,
            },
            `Status: ${entry.status}`
          )
        );
      }
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
          React.createElement('p', { key: 'summary' }, `Summary: ${entry.summaryPath}`)
        );
      }
      if (entry.stdoutPath) {
        elements.push(
          React.createElement('p', { key: 'stdout' }, `Stdout: ${entry.stdoutPath}`)
        );
      }
      if (entry.stderrPath) {
        elements.push(
          React.createElement('p', { key: 'stderr' }, `Stderr: ${entry.stderrPath}`)
        );
      }
      if (entry.startedAt) {
        elements.push(
          React.createElement('p', { key: 'started' }, `Started: ${entry.startedAt}`)
        );
      }
      if (entry.completedAt) {
        elements.push(
          React.createElement('p', { key: 'completed' }, `Completed: ${entry.completedAt}`)
        );
      }
      if (entry.sandboxSummary) {
        elements.push(
          React.createElement('p', { key: 'sandbox' }, entry.sandboxSummary)
        );
      }
      if (entry.sandboxOverrides && Object.keys(entry.sandboxOverrides).length) {
        elements.push(
          React.createElement(
            'div',
            { key: 'overrides' },
            [
              React.createElement('p', { key: 'overrides-label' }, 'Sandbox overrides:'),
              React.createElement(
                'ul',
                { key: 'overrides-list' },
                Object.entries(entry.sandboxOverrides).map(([key, value]) =>
                  React.createElement('li', { key }, `${key}: ${value}`)
                )
              ),
            ]
          )
        );
      }
      if (Array.isArray(entry.warnings) && entry.warnings.length) {
        elements.push(
          React.createElement(
            'div',
            { key: 'warnings' },
            [
              React.createElement('p', { key: 'warnings-label' }, 'Warnings:'),
              React.createElement(
                'ul',
                { key: 'warnings-list' },
                entry.warnings.map((warning, index) =>
                  React.createElement('li', { key: `${index}-${warning}` }, warning)
                )
              ),
            ]
          )
        );
      }
      if (entry.contract) {
        const contract = entry.contract;
        elements.push(
          React.createElement(
            'div',
            { key: 'contract' },
            [
              React.createElement(
                'p',
                { key: 'contract-summary' },
                `Contract suite: ${contract.suite} (${contract.status})`
              ),
              React.createElement(
                'p',
                { key: 'contract-counts' },
                `Tests: ${contract.passed}/${contract.total} passed, ${contract.failed} failed, ${contract.skipped} skipped`
              ),
              contract.sandboxed
                ? React.createElement(
                    'p',
                    { key: 'contract-sandboxed', className: 'mission-stage__warning' },
                    'Sandbox contract stub executed'
                  )
                : null,
              Array.isArray(contract.notes) && contract.notes.length
                ? React.createElement(
                    'ul',
                    { key: 'contract-notes' },
                    contract.notes.map((note, index) =>
                      React.createElement('li', { key: `${index}-note` }, note)
                    )
                  )
                : null,
              Array.isArray(contract.tests) && contract.tests.length
                ? React.createElement(
                    'ul',
                    { key: 'contract-tests', className: 'mission-stage__list' },
                    contract.tests.map((test, index) => {
                      const name = test.name || test.id || `test-${index + 1}`;
                      const reason = test.reason ? ` – ${test.reason}` : '';
                      return React.createElement(
                        'li',
                        { key: test.id || `${name}-${index}` },
                        `${name}: ${test.status}${reason}`
                      );
                    })
                  )
                : null,
              contract.fixtures
                ? React.createElement(
                    'pre',
                    { key: 'contract-fixtures', className: 'mission-stage__metrics' },
                    JSON.stringify(contract.fixtures, null, 2)
                  )
                : null,
            ].filter(Boolean)
          )
        );
      }
      if (Array.isArray(entry.migrationEntries) && entry.migrationEntries.length) {
        elements.push(
          React.createElement(
            'div',
            { key: 'migration' },
            [
              React.createElement('p', { key: 'migration-label' }, 'Migration entries:'),
              React.createElement(
                'ul',
                { key: 'migration-list' },
                entry.migrationEntries.map((item, index) => {
                  const legacy = item?.legacy_entry ?? 'unknown';
                  const neo = item?.neo_module ?? 'unknown';
                  const status = item?.status ? ` (${item.status})` : '';
                  return React.createElement(
                    'li',
                    { key: `${index}-${legacy}` },
                    `${legacy} → ${neo}${status}`
                  );
                })
              ),
            ]
          )
        );
      }
      if (entry.artifacts && Object.keys(entry.artifacts).length) {
        elements.push(
          React.createElement(
            'div',
            { key: 'artifacts' },
            [
              React.createElement('p', { key: 'artifacts-label' }, 'Artifacts:'),
              React.createElement(
                'ul',
                { key: 'artifacts-list' },
                Object.entries(entry.artifacts).map(([key, value]) =>
                  React.createElement('li', { key }, `${key}: ${value}`)
                )
              ),
            ]
          )
        );
      }
      if (entry.notes) {
        elements.push(
          React.createElement('p', { key: 'notes' }, `Notes: ${entry.notes}`)
        );
      }
      return React.createElement(
        'div',
        { className: 'mission-stage__details', key: `${id}-details` },
        elements
      );
    },
    [stageDResults]
  );

  const createStageCAction = React.useCallback(
    ({ id, label, endpoint }) => {
      const execute = async () => {
        const startedAt = new Date().toISOString();
        setStageCResults((prev) => ({
          ...prev,
          [id]: {
            status: 'running',
            startedAt,
            completedAt: null,
            error: null,
            metrics: null,
            responseStatus: null,
            rawResponse: null,
            runId: null,
            logDir: null,
            summaryPath: null,
            stdoutPath: null,
            stderrPath: null,
            stderrTail: null,
            artifacts: null,
          },
        }));

        const response = await fetch(`${BASE_URL}${endpoint}`, { method: 'POST' });
        const raw = await response.text();
        let data = null;
        let parseError = null;
        if (raw.trim()) {
          try {
            data = JSON.parse(raw);
          } catch (err) {
            parseError = err;
          }
        }
        if (parseError) {
          const message = `Failed to parse response JSON: ${parseError.message}`;
          const completedAt = new Date().toISOString();
          setStageCResults((prev) => ({
            ...prev,
            [id]: {
              ...(prev[id] ?? {}),
              status: 'error',
              error: message,
              completedAt,
              responseStatus: response.status,
              rawResponse: raw,
              artifacts: (prev[id] ?? {}).artifacts ?? null,
            },
          }));
          appendLog(
            formatStageABlock(label, {
              status: 'error',
              error: message,
              raw,
            })
          );
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
          responseStatus: response.status,
          rawResponse: raw,
          runId: payload.run_id ?? null,
          logDir: payload.log_dir ?? null,
          summaryPath: payload.summary_path ?? null,
          stdoutPath: payload.stdout_path ?? null,
          stderrPath: payload.stderr_path ?? null,
          stderrTail: payload.stderr_tail ?? null,
          stderr: payload.stderr ?? null,
          artifacts: payload.artifacts ?? null,
        };
        if (payload.status !== 'success') {
          baseUpdate.error = payload.error || payload.detail || `HTTP ${response.status}`;
          setStageCResults((prev) => ({ ...prev, [id]: baseUpdate }));
          const error = new Error(baseUpdate.error);
          error.stageResult = payload;
          throw error;
        }
        setStageCResults((prev) => ({ ...prev, [id]: baseUpdate }));
        return payload;
      };

      const action = createLoggedAction(id, label, execute, {
        onError: (error) => {
          if (error?.stageResult) {
            return;
          }
          setStageCResults((prev) => ({
            ...prev,
            [id]: {
              ...(prev[id] ?? {}),
              status: 'error',
              error: error?.message ?? String(error),
              completedAt: new Date().toISOString(),
              artifacts: (prev[id] ?? {}).artifacts ?? null,
            },
          }));
          appendLog(
            formatStageABlock(label, {
              status: 'error',
              error: error?.message ?? String(error),
            })
          );
        },
      });

      return {
        ...action,
        status: stageCResults[id]?.status,
        renderDetails: () => renderStageCDetails(id),
      };
    },
    [appendLog, createLoggedAction, formatStageABlock, renderStageCDetails, stageCResults]
  );

  const createStageDAction = React.useCallback(
    ({ id, label, endpoint }) => {
      const execute = async () => {
        const startedAt = new Date().toISOString();
        setStageDResults((prev) => ({
          ...prev,
          [id]: {
            ...(prev[id] ?? stageDFallback[id] ?? {}),
            status: 'running',
            startedAt,
            completedAt: null,
            responseStatus: null,
            error: null,
            sandboxSummary: null,
            sandboxOverrides: null,
            warnings: null,
            contract: null,
            migrationEntries: null,
            artifacts: null,
          },
        }));
        const { response, data, raw, parseError } = await streamJsonPost(
          endpoint,
          label
        );
        if (parseError) {
          const message = `Failed to parse response JSON: ${parseError.message}`;
          const completedAt = new Date().toISOString();
          setStageDResults((prev) => ({
            ...prev,
            [id]: {
              ...(prev[id] ?? stageDFallback[id] ?? {}),
              status: 'error',
              startedAt,
              completedAt,
              error: message,
              responseStatus: response?.status ?? null,
              warnings: null,
              artifacts:
                (prev[id] ?? stageDFallback[id] ?? {}).artifacts ?? null,
            },
          }));
          appendLog(
            formatStageABlock(label, {
              status: 'error',
              error: message,
              raw,
            })
          );
          throw new Error(message);
        }
        const payload = {
          status: response.ok ? 'success' : 'error',
          status_code: response.status,
          ...(data ?? {}),
        };
        appendLog(formatStageABlock(label, payload));
        const completedAt = new Date().toISOString();
        const fallback = stageDFallback[id] ?? {};
        const summary =
          payload.summary && typeof payload.summary === 'object'
            ? payload.summary
            : {};
        const contractSuite =
          summary.contract_suite && typeof summary.contract_suite === 'object'
            ? summary.contract_suite
            : null;
        const contract = contractSuite
          ? {
              suite: contractSuite.suite ?? label,
              status: contractSuite.status ?? 'unknown',
              passed: contractSuite.passed ?? 0,
              failed: contractSuite.failed ?? 0,
              skipped: contractSuite.skipped ?? 0,
              total:
                contractSuite.total ??
                (Array.isArray(contractSuite.tests)
                  ? contractSuite.tests.length
                  : 0),
              sandboxed: Boolean(contractSuite.sandboxed),
              notes: Array.isArray(contractSuite.notes)
                ? contractSuite.notes
                : contractSuite.notes
                ? [contractSuite.notes]
                : [],
              tests: Array.isArray(contractSuite.tests)
                ? contractSuite.tests
                : [],
              fixtures:
                typeof contractSuite.fixtures === 'object'
                  ? contractSuite.fixtures
                  : null,
            }
          : null;
        const warnings = Array.isArray(summary.warnings)
          ? summary.warnings
          : [];
        const sandboxOverrides =
          summary.sandbox_overrides &&
          typeof summary.sandbox_overrides === 'object'
            ? summary.sandbox_overrides
            : null;
        const baseUpdate = {
          status: payload.status,
          startedAt,
          completedAt,
          responseStatus: response.status,
          runId: payload.run_id ?? summary.run_id ?? fallback.runId ?? null,
          logDir: payload.log_dir ?? summary.log_dir ?? fallback.logDir ?? null,
          summaryPath:
            payload.summary_path ?? summary.summary_path ?? fallback.summaryPath ?? null,
          stdoutPath:
            payload.stdout_path ?? summary.stdout_path ?? fallback.stdoutPath ?? null,
          stderrPath:
            payload.stderr_path ?? summary.stderr_path ?? fallback.stderrPath ?? null,
          sandboxSummary: summary.sandbox_summary ?? null,
          sandboxOverrides,
          warnings,
          contract,
          migrationEntries: Array.isArray(summary.migration_entries)
            ? summary.migration_entries
            : null,
          artifacts:
            payload.artifacts ?? summary.artifacts ?? fallback.artifacts ?? null,
          error: null,
          notes: fallback.notes ?? null,
        };
        if (payload.status !== 'success') {
          baseUpdate.error =
            payload.error ||
            payload.detail ||
            (warnings && warnings.length ? warnings.join('; ') : null) ||
            `HTTP ${response.status}`;
          setStageDResults((prev) => ({ ...prev, [id]: baseUpdate }));
          const error = new Error(baseUpdate.error ?? `${label} failed`);
          error.stageResult = payload;
          throw error;
        }
        setStageDResults((prev) => ({ ...prev, [id]: baseUpdate }));
        return payload;
      };

      const action = createLoggedAction(id, label, execute, {
        onError: (error) => {
          if (error?.stageResult) {
            return;
          }
          setStageDResults((prev) => ({
            ...prev,
            [id]: {
              ...(prev[id] ?? stageDFallback[id] ?? {}),
              status: 'error',
              completedAt: new Date().toISOString(),
              error: error?.message ?? String(error),
              artifacts:
                (prev[id] ?? stageDFallback[id] ?? {}).artifacts ?? null,
            },
          }));
          appendLog(
            formatStageABlock(label, {
              status: 'error',
              error: error?.message ?? String(error),
            })
          );
        },
      });

      return {
        ...action,
        status: stageDResults[id]?.status ?? stageDFallback[id]?.status ?? null,
        renderDetails: () => renderStageDDetails(id),
      };
    },
    [
      appendLog,
      createLoggedAction,
      formatStageABlock,
      renderStageDDetails,
      stageDResults,
      streamJsonPost,
    ]
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
        groups: [
          {
            id: 'stage-a-milestones',
            title: 'Milestone Controls',
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
            ],
          },
          {
            id: 'stage-a-extended',
            title: 'Extended Automation',
            actions: [
              createStageAAction({
                id: 'stage-a3-gate-shakeout',
                label: 'Stage A3 – Gate Shakeout',
                endpoint: '/alpha/stage-a3-gate-shakeout',
              }),
            ],
          },
        ],
      },
      {
        id: 'stage-b',
        title: stageTitles['stage-b'],
        groups: [
          {
            id: 'stage-b-milestones',
            title: 'Milestone Controls',
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
            ],
          },
          {
            id: 'stage-b-operations',
            title: 'Operational Utilities',
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
        ],
      },
      {
        id: 'stage-c',
        title: stageTitles['stage-c'],
        groups: [
          {
            id: 'stage-c-milestones',
            title: 'Milestone Controls',
            actions: [
              createStageCAction({
                id: 'stage-c1-exit-checklist',
                label: 'Stage C1 – Exit Checklist',
                endpoint: '/alpha/stage-c1-exit-checklist',
              }),
              createStageCAction({
                id: 'stage-c2-demo-storyline',
                label: 'Stage C2 – Demo Storyline',
                endpoint: '/alpha/stage-c2-demo-storyline',
              }),
            ],
          },
          {
            id: 'stage-c-readiness',
            title: 'Readiness & MCP Drills',
            actions: [
              createStageCAction({
                id: 'stage-c3-readiness-sync',
                label: 'Stage C3 – Readiness Sync',
                endpoint: '/alpha/stage-c3-readiness-sync',
              }),
              createStageCAction({
                id: 'stage-c4-operator-mcp-drill',
                label: 'Stage C4 – Operator MCP Drill',
                endpoint: '/alpha/stage-c4-operator-mcp-drill',
              }),
            ],
          },
          {
            id: 'stage-c-escalation',
            title: 'Escalation',
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
      },
      {
        id: 'stage-d',
        title: stageTitles['stage-d'],
        groups: [
          {
            id: 'stage-d-verification',
            title: 'Neo-APSU Sandbox',
            actions: [
              createStageDAction({
                id: 'stage-d1-neoapsu-memory',
                label: 'Stage D1 – Neo-APSU Memory',
                endpoint: '/alpha/stage-d1-neoapsu-memory',
              }),
              createStageDAction({
                id: 'stage-d2-neoapsu-crown',
                label: 'Stage D2 – Neo-APSU Crown',
                endpoint: '/alpha/stage-d2-neoapsu-crown',
              }),
              createStageDAction({
                id: 'stage-d3-neoapsu-identity',
                label: 'Stage D3 – Neo-APSU Identity',
                endpoint: '/alpha/stage-d3-neoapsu-identity',
              }),
            ],
          },
        ],
      },
    ],
    [
      createLoggedAction,
      createStageAAction,
      createStageBAction,
      createStageCAction,
      createStageDAction,
      logSuccess,
    ]
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
