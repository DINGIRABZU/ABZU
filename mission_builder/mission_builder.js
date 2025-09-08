/* global Blockly */

const workspace = Blockly.inject('blocklyDiv', {
  toolbox: document.getElementById('toolbox')
});

Blockly.defineBlocksWithJsonArray([
  {
    "type": "mission_event",
    "message0": "event %1 capability %2",
    "args0": [
      { "type": "field_input", "name": "EVENT", "text": "event_type" },
      { "type": "field_input", "name": "CAPABILITY", "text": "capability" }
    ],
    "previousStatement": null,
    "nextStatement": null,
    "colour": 230,
    "tooltip": "Emit an event with a capability",
    "helpUrl": ""
  }
  ,
  {
    "type": "ignite",
    "message0": "ignite target %1",
    "args0": [
      { "type": "field_input", "name": "TARGET", "text": "crown" }
    ],
    "previousStatement": null,
    "nextStatement": null,
    "colour": 0,
    "tooltip": "Ignite a target",
    "helpUrl": ""
  },
  {
    "type": "query_memory",
    "message0": "query memory %1",
    "args0": [
      { "type": "field_input", "name": "QUERY", "text": "search" }
    ],
    "previousStatement": null,
    "nextStatement": null,
    "colour": 120,
    "tooltip": "Query stored memories",
    "helpUrl": ""
  },
  {
    "type": "dispatch_agent",
    "message0": "dispatch agent %1 task %2",
    "args0": [
      { "type": "field_input", "name": "AGENT", "text": "agent" },
      { "type": "field_input", "name": "TASK", "text": "task" }
    ],
    "previousStatement": null,
    "nextStatement": null,
    "colour": 60,
    "tooltip": "Dispatch an agent",
    "helpUrl": ""
  }
]);

function missionToJson() {
  const mission = [];
  const blocks = workspace.getTopBlocks(true);
  for (const block of blocks) {
    if (block.type === 'mission_event') {
      mission.push({
        event_type: block.getFieldValue('EVENT'),
        payload: { capability: block.getFieldValue('CAPABILITY') }
      });
    } else if (block.type === 'ignite') {
      mission.push({
        event_type: 'ignite',
        payload: {
          capability: 'ignite',
          target: block.getFieldValue('TARGET')
        }
      });
    } else if (block.type === 'query_memory') {
      mission.push({
        event_type: 'query_memory',
        payload: {
          capability: 'query_memory',
          query: block.getFieldValue('QUERY')
        }
      });
    } else if (block.type === 'dispatch_agent') {
      mission.push({
        event_type: 'dispatch',
        payload: {
          capability: 'dispatch',
          agent: block.getFieldValue('AGENT'),
          task: block.getFieldValue('TASK')
        }
      });
    }
  }
  return mission;
}

function downloadMission() {
  const data = JSON.stringify(missionToJson(), null, 2);
  const blob = new Blob([data], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'mission.json';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

async function saveMission() {
  const name = prompt('Mission name');
  if (!name) return;
  const mission = missionToJson();
  await fetch('/missions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, mission })
  });
}

window.downloadMission = downloadMission;
window.saveMission = saveMission;
