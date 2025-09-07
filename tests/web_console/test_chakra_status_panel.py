from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
GD_DIR = ROOT / "web_console" / "game_dashboard"


def test_dashboard_imports_chakra_status_panel() -> None:
    js = (GD_DIR / "dashboard.js").read_text(encoding="utf-8")
    assert "chakra_status_panel/chakra_status_panel.js" in js
    assert "ChakraStatusPanel" in js


def test_chakra_status_panel_has_id() -> None:
    comp = (GD_DIR / "chakra_status_panel" / "chakra_status_panel.js").read_text(
        encoding="utf-8"
    )
    assert "chakra-status-panel" in comp


def test_chakra_status_panel_renders_mock_data() -> None:
    js_path = GD_DIR / "chakra_status_panel" / "chakra_status_panel.js"
    script = """
const fs = require('fs');
let code = fs.readFileSync('{js_path}', 'utf8');
code = code.replace(/import[^\n]+\n/g, '');
code = code.replace('export default function ChakraStatusPanel', 'function ChakraStatusPanel');
code += '\nreturn ChakraStatusPanel;';
const React = {{
  createElement: (t, p, ...c) => ({{ t, p: p || {{}}, c }}),
  useState: (i) => [i, () => {{}}],
  useEffect: () => {{}}
}};
function render(n) {{
  if (typeof n === 'string') return n;
  const attrs = Object.entries(n.p || {{}}).map(([k,v]) => ` ${k}="${v}"`).join('');
  return `<${{n.t}}${{attrs}}>${{(n.c || []).map(render).join('')}}</${{n.t}}>`;
}}
const Comp = new Function('React', code)(React);
const html = render(Comp({{ initialData: {{ heartbeats: {{ alpha: 1.2 }}, components: {{ state_validator: '0.2.2' }} }} }}));
console.log(html);
""".format(js_path=js_path.as_posix())
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)
    output = result.stdout.strip()
    assert "alpha" in output
    assert "state_validator" in output
