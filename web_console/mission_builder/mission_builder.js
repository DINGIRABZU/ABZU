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

window.downloadMission = downloadMission;
