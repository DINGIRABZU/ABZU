import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GD_DIR = ROOT / "web_console" / "game_dashboard"


def test_dashboard_imports_connectors_panel() -> None:
    js = (GD_DIR / "dashboard.js").read_text(encoding="utf-8")
    assert "connectors_panel/connectors_panel.js" in js
    assert "ConnectorsPanel" in js


def test_connectors_panel_has_id() -> None:
    comp = (GD_DIR / "connectors_panel" / "connectors_panel.js").read_text(
        encoding="utf-8"
    )
    assert "connectors-panel" in comp


def test_connector_panel_updates_on_events() -> None:
    js_path = GD_DIR / "connectors_panel" / "connectors_panel.js"
    script = f"""
const fs = require('fs');
let code = fs.readFileSync('{js_path.as_posix()}', 'utf8');
code = code.replace(/import[^\n]+\n/g, '');
code = code.replace('export default function ConnectorsPanel', 'function ConnectorsPanel');
code += '\nreturn ConnectorsPanel;';
let state = [];
let idx = 0;
const React = {{
  createElement: (t,p,...c) => ({{ t, p: p || {{}}, c }}),
  useState: (init) => {{
    const i = idx;
    state[i] = state[i] !== undefined ? state[i] : init;
    function setState(v) {{ state[i] = typeof v === 'function' ? v(state[i]) : v; }}
    idx++;
    return [state[i], setState];
  }},
  useEffect: (fn) => fn()
}};
let handlers = {{}};
const bus = {{
  subscribe: (ch, cb) => {{ (handlers[ch] = handlers[ch] || []).push(cb); return () => {{}}; }},
  publish: (ch, payload) => {{ (handlers[ch] || []).forEach(cb => cb(payload)); }}
}};
function render(n) {{
  if (typeof n === 'string') return n;
  return `<${{n.t}}>${{(n.c||[]).map(render).join('')}}</${{n.t}}>`;
}}
const Comp = new Function('React', code)(React);
let view = Comp({{ bus }});
bus.publish('connectors', {{ name: 'alpha', status: 'down' }});
idx = 0;
view = Comp({{ bus }});
console.log(render(view));
"""
    result = subprocess.run(
        ["node", "-e", script], capture_output=True, text=True, check=True
    )
    output = result.stdout.strip()
    assert "alpha" in output
    assert "down" in output
