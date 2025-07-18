import sys
import asyncio
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import servant_model_manager as smm


async def _echo(prompt: str) -> str:
    return f"echo:{prompt}"


def test_register_and_invoke():
    smm.register_model("echo", _echo)
    out = asyncio.run(smm.invoke("echo", "hi"))
    assert out == "echo:hi"


def test_subprocess_model(tmp_path):
    script = tmp_path / "echo.py"
    script.write_text("import sys; print(sys.stdin.read())", encoding="utf-8")
    smm.register_subprocess_model("sp", [sys.executable, str(script)])
    out = smm.invoke_sync("sp", "test")
    assert out.strip() == "test"


def test_kimi_k2_registration():
    smm.register_model("kimi_k2", _echo)
    out = asyncio.run(smm.invoke("kimi_k2", "ping"))
    assert out == "echo:ping"
