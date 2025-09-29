import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MISSION_MAP = ROOT / "web_console" / "game_dashboard" / "mission_map.js"


def _render_summary() -> dict:
    script = f"""
const fs = require('fs');
let code = fs.readFileSync('{MISSION_MAP.as_posix()}', 'utf8');
code = code.replace(/import[^;]+;/g, '');
code = code.replace('export default function MissionMap', 'function MissionMap');
code += '\nreturn MissionMap;';
const React = {{
  Fragment: 'fragment',
  createElement: (type, props, ...children) => {{
    const flat = [];
    const flatten = (items) => {{
      items.forEach((item) => {{
        if (Array.isArray(item)) {{
          flatten(item);
        }} else if (item !== undefined) {{
          flat.push(item);
        }}
      }});
    }};
    flatten(children);
    return {{ type, props: props || {{}}, children: flat }};
  }},
  useMemo: (factory) => factory(),
  useEffect: () => {{}},
  useState: (initial) => [initial, () => {{}}],
}};
global.document = {{ getElementById: () => null }};
global.window = {{
  addEventListener: () => {{}},
  removeEventListener: () => {{}},
}};
global.navigator = {{ getGamepads: () => [] }};
global.requestAnimationFrame = () => 0;
global.cancelAnimationFrame = () => {{}};
const Comp = new Function('React', code)(React);
const tree = Comp({{
  stages: [
    {{
      id: 'stage-a',
      title: 'Stage A',
      groups: [
        {{
          id: 'stage-a-milestones',
          title: 'Milestone Controls',
          actions: [
            {{ id: 'action-a1', label: 'A1', action: () => {{}} }},
          ],
        }},
        {{
          id: 'stage-a-empty',
          title: 'Extended Automation',
          actions: [],
        }}
      ],
    }},
  ],
}});
const summary = {{ groupTitles: [], emptyGroups: 0, buttonIds: [] }};
function walk(node) {{
  if (!node || typeof node !== 'object') return;
  const props = node.props || {{}};
  if (props.className === 'mission-stage__group-title' && node.children.length) {{
    summary.groupTitles.push(node.children[0]);
  }}
  if (props.className === 'mission-stage__empty') {{
    summary.emptyGroups += 1;
  }}
  if (props.id) {{
    summary.buttonIds.push(props.id);
  }}
  (node.children || []).forEach((child) => walk(child));
}}
walk(tree);
console.log(JSON.stringify(summary));
"""
    result = subprocess.run(
        ["node", "-e", script], capture_output=True, text=True, check=True
    )
    return json.loads(result.stdout)


def test_mission_map_groups_rendered() -> None:
    summary = _render_summary()
    assert "Milestone Controls" in summary["groupTitles"]
    assert "Extended Automation" in summary["groupTitles"]
    assert summary["emptyGroups"] >= 1
    assert "action-a1-btn" in summary["buttonIds"]
