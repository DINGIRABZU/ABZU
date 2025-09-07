from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
GD_DIR = ROOT / "web_console" / "game_dashboard"


def test_dashboard_imports_agent_status_panel() -> None:
    js = (GD_DIR / "dashboard.js").read_text(encoding="utf-8")
    assert "agent_status_panel.js" in js
    assert "AgentStatusPanel" in js


def test_agent_status_panel_has_id() -> None:
    comp = (GD_DIR / "agent_status_panel.js").read_text(encoding="utf-8")
    assert "agent-status-panel" in comp


def test_agent_status_panel_renders_mock_data() -> None:
    js_path = GD_DIR / "agent_status_panel.js"
    script = """
const fs = require('fs');
let code = fs.readFileSync('{js_path}', 'utf8');
code = code.replace(/import[^\n]+\n/, '');
code = code.replace(
  'export default function AgentStatusPanel',
  'function AgentStatusPanel'
);
code += '\nreturn AgentStatusPanel;';
const React = {{
  createElement: (t, p, ...c) => ({{ t, p: p || {{}}, c }}),
  useState: (i) => [i, () => {{}}],
  useEffect: () => {{}}
}};
function render(n) {{
  if (typeof n === 'string') return n;
  return `<${{n.t}}>${{(n.c || []).map(render).join('')}}</${{n.t}}>`;
}}
const Comp = new Function('React', code)(React);
const html = render(
  Comp({{
    initialData: {{
      alpha: {{ last_beat: 1, last_action: 'move', chakra: 'aligned' }}
    }}
  }})
);
console.log(html);
""".format(
        js_path=js_path.as_posix()
    )
    result = subprocess.run(
        ["node", "-e", script], capture_output=True, text=True, check=True
    )
    output = result.stdout.strip()
    assert "alpha" in output
    assert "move" in output
    assert "aligned" in output
