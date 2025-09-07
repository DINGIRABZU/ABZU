from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GD_DIR = ROOT / "web_console" / "game_dashboard"


def test_dashboard_imports_memory_panel() -> None:
    js = (GD_DIR / "dashboard.js").read_text(encoding="utf-8")
    assert "memory_panel/memory_panel.js" in js
    assert "MemoryPanel" in js


def test_memory_panel_has_id() -> None:
    comp = (GD_DIR / "memory_panel" / "memory_panel.js").read_text(encoding="utf-8")
    assert "memory-panel" in comp


def test_memory_panel_renders_mock_data() -> None:
    js_path = GD_DIR / "memory_panel" / "memory_panel.js"
    script = f"""
const fs = require('fs');
let code = fs.readFileSync('{js_path.as_posix()}', 'utf8');
code = code.replace(/import[^\n]+\n/g, '');
code = code.replace('export default function MemoryPanel', 'function MemoryPanel');
code += '\nreturn MemoryPanel;';
const React = {{
  createElement: (t, p, ...c) => ({{ t, p: p || {{}}, c }}),
  useState: (i) => [i, () => {{}}],
  useEffect: (fn) => fn()
}};
global.fetch = async () => ({{ json: async () => ({{ chakras: {{ root: {{ count: 5, last_heartbeat: 42 }} }} }}) }});
const Comp = new Function('React', code)(React);
function render(n) {{
  if (typeof n === 'string') return n;
  return `<${{n.t}}>${{(n.c || []).map(render).join('')}}</${{n.t}}>`;
}}
const html = render(Comp());
console.log(html);
"""
    result = subprocess.run(
        ["node", "-e", script], capture_output=True, text=True, check=True
    )
    output = result.stdout.strip()
    assert "root" in output
    assert "5" in output
