import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GD_DIR = ROOT / "web_console" / "game_dashboard"


def test_dashboard_imports_self_healing_panel() -> None:
    js = (GD_DIR / "dashboard.js").read_text(encoding="utf-8")
    assert "self_healing_panel/self_healing_panel.js" in js
    assert "SelfHealingPanel" in js


def test_self_healing_panel_has_id() -> None:
    comp = (GD_DIR / "self_healing_panel" / "self_healing_panel.js").read_text(
        encoding="utf-8"
    )
    assert "self-healing-panel" in comp


def test_self_healing_panel_renders_mock_events() -> None:
    js_path = GD_DIR / "self_healing_panel" / "self_healing_panel.js"
    script = f"""
const fs = require('fs');
let code = fs.readFileSync('{js_path.as_posix()}', 'utf8');
code = code.replace(/import[^\n]+\n/g, '');
code = code.replace('export default function SelfHealingPanel', 'function SelfHealingPanel');
code += '\nreturn SelfHealingPanel;';
let state = [];
let idx = 0;
const React = {{
  createElement: (t,p,...c) => ({{ t, p: p || {{}}, c }}),
  useState: (init) => {{
    const i = idx;
    state[i] = state[i] !== undefined ? state[i] : init;
    function setState(v) {{ state[i] = v; }}
    idx++;
    return [state[i], setState];
  }},
  useEffect: (fn) => fn()
}};
class WS {{
  constructor() {{ WS.instance = this; }}
  close() {{}}
}}
global.WebSocket = WS;
const Comp = new Function('React', code)(React);
idx = 0;
let view = Comp();
WS.instance.onmessage({{ data: JSON.stringify({{ component: 'root', gap: 3, agent: 'alpha', result: 'patched' }}) }});
idx = 0;
view = Comp();
function render(n) {{
  if (typeof n === 'string') return n;
  return `<${{n.t}}>${{(n.c||[]).map(render).join('')}}</${{n.t}}>`;
}}
console.log(render(view));
"""
    result = subprocess.run(
        ["node", "-e", script], capture_output=True, text=True, check=True
    )
    output = result.stdout.strip()
    assert "root: 3" in output
    assert "root: alpha" in output
    assert "root: patched" in output
