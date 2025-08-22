import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location(
    "task_parser", ROOT / "src" / "core" / "task_parser.py"
)
task_parser = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(task_parser)


def test_task_parser_performance():
    text = "appear to me and initiate sacred communion" * 20
    start = time.perf_counter()
    for _ in range(1000):
        task_parser.parse(text)
    duration = time.perf_counter() - start
    # Ensure the parser remains efficient
    assert duration < 0.5
