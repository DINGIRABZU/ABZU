from __future__ import annotations

from pathlib import Path

from razar import boot_orchestrator

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
LOGS_DIR = ROOT / "logs"


def boot_sequence(config_path: Path | None = None) -> dict[str, str]:
    """Run the minimal boot sequence using :mod:`razar.boot_orchestrator`.

    The helper ensures the data and log directories exist, loads the
    component configuration, and launches each component. It waits for all
    processes to exit before returning a mapping with the resolved paths so
    callers can verify initialization if needed.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    cfg = config_path or Path(__file__).with_name("boot_config.json")
    components = boot_orchestrator.load_config(cfg)
    procs = [boot_orchestrator.launch_component(c) for c in components]
    for proc in procs:
        proc.wait()

    return {"data_dir": str(DATA_DIR), "logs_dir": str(LOGS_DIR)}


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    boot_sequence()
