from __future__ import annotations

"""Command line launcher for the development agent cycle."""

import argparse
import logging
import os
import json
from pathlib import Path

from tools.dev_orchestrator import DevAssistantService, run_dev_cycle


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
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--objective", help="Objective for a single run")
    group.add_argument("--watch", action="store_true", help="Watch logs and run cycles")
    group.add_argument(
        "--stop", action="store_true", help="Signal a running watcher to stop"
    )
    parser.add_argument(
        "--planner-model", help="Endpoint used by the planner agent"
    )
    parser.add_argument(
        "--coder-model", help="Endpoint used by the coder agent",
    )
    parser.add_argument(
        "--reviewer-model", help="Endpoint used by the reviewer agent",
    )
    parser.add_argument(
        "--log-path", default="logs/dev_agent.log", help="Log file monitored"
    )
    parser.add_argument(
        "--objective-map",
        help="JSON file mapping log markers to objectives for --watch",
    )
    parser.add_argument(
        "--max-iterations", type=int, help="Limit on tasks executed",
    )
    parser.add_argument(
        "--config", help="Path to JSON config with environment settings",
    )
    args = parser.parse_args()

    load_env(Path("secrets.env"))

    log_path = Path(args.log_path)
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

    if args.config:
        try:
            data = json.loads(Path(args.config).read_text())
            for key, value in data.items():
                os.environ[key.upper()] = str(value)
        except Exception as exc:  # pragma: no cover - best effort
            logger.error("Failed to load config: %s", exc)

    if args.planner_model:
        os.environ["PLANNER_MODEL"] = args.planner_model
    if args.coder_model:
        os.environ["CODER_MODEL"] = args.coder_model
    if args.reviewer_model:
        os.environ["REVIEWER_MODEL"] = args.reviewer_model

    if args.stop:
        stop_file = log_path.with_suffix(".stop")
        stop_file.touch()
        logger.info("Stop signal written to %s", stop_file)
        return 0

    if args.watch:
        objectives = None
        if args.objective_map:
            try:
                objectives = json.loads(Path(args.objective_map).read_text())
            except Exception as exc:  # pragma: no cover - best effort
                logger.error("Failed to load objective map: %s", exc)
        service = DevAssistantService(
            repo=Path.cwd(), log_path=log_path, objectives=objectives
        )
        logger.info("Starting watcher; press Ctrl+C or run with --stop to end")
        try:
            service.run_forever()
        except KeyboardInterrupt:
            logger.info("Watcher interrupted by user")
        return 0

    logger.info("Starting development cycle: %s", args.objective)

    result = run_dev_cycle(
        args.objective, repo=Path.cwd(), max_iterations=args.max_iterations
    )

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
