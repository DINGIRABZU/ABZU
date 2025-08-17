from __future__ import annotations

"""Command line launcher for the development agent cycle."""

import argparse
import logging
import os
from pathlib import Path

from tools.dev_orchestrator import run_dev_cycle


def load_env(path: Path) -> None:
    """Load environment variables from ``path`` if it exists."""
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run development agents")
    parser.add_argument("--objective", required=True, help="Objective for the cycle")
    parser.add_argument(
        "--planner-model", help="LLM or endpoint used by the planner agent"
    )
    args = parser.parse_args()

    load_env(Path("secrets.env"))
    if args.planner_model:
        os.environ["PLANNER_MODEL"] = args.planner_model

    log_path = Path("logs/dev_agent.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
    )
    logger = logging.getLogger("dev_agent_runner")
    logger.info("Starting development cycle: %s", args.objective)

    result = run_dev_cycle(args.objective, repo=Path.cwd())

    for step in result.get("plan", []):
        logger.info("Planned step: %s", step)
    for item in result.get("results", []):
        logger.info("Task completed: %s", item.get("task"))

    tests = result.get("tests")
    if tests is not None:
        logger.info("Tests exit code: %s", tests.get("returncode"))

    summary = {
        "objective": result.get("objective"),
        "steps": result.get("plan"),
        "tests": tests,
    }
    logger.info("Summary: %s", summary)
    logger.info("Development cycle finished")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
