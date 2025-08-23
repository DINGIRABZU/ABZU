from __future__ import annotations

"""Command line launcher for the development agent cycle."""

import argparse
import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path

from env_validation import check_required
from tools.dev_orchestrator import DevAssistantService, run_dev_cycle


def load_env(path: Path) -> None:
    """Load environment variables from ``path`` if it exists.

    Lines without ``=`` or with empty keys are logged and ignored. Loaded
    variables are exported so that spawned subprocesses inherit them.
    """

    logger = logging.getLogger(__name__)

    if not path.is_file():
        return

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            logger.warning("Skipping malformed line without '=': %s", line)
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            logger.warning("Skipping line with empty key: %s", line)
            continue
        value = value.strip()
        os.environ[key] = value
        os.putenv(key, value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run development agents")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--objective", help="Objective for a single run")
    group.add_argument(
        "--watch",
        action="store_true",
        help="Watch logs and run cycles",
    )
    group.add_argument(
        "--stop", action="store_true", help="Signal a running watcher to stop"
    )
    group.add_argument(
        "--triage",
        nargs="+",
        metavar="PATH",
        help="Run pytest on selected paths and trigger agent fixes",
    )
    parser.add_argument(
        "--planner-model",
        help="Endpoint used by the planner agent",
    )
    parser.add_argument(
        "--coder-model",
        help="Endpoint used by the coder agent",
    )
    parser.add_argument(
        "--reviewer-model",
        help="Endpoint used by the reviewer agent",
    )
    parser.add_argument(
        "--log-path", default="logs/dev_agent.log", help="Log file monitored"
    )
    parser.add_argument(
        "--objective-map",
        help="JSON file mapping log markers to objectives for --watch",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        help="Limit on tasks executed",
    )
    parser.add_argument(
        "--config",
        help="Path to JSON config with environment settings",
    )
    args = parser.parse_args()

    if args.objective is not None and not args.objective.strip():
        parser.error("--objective cannot be empty")
    if args.max_iterations is not None and args.max_iterations < 1:
        parser.error("--max-iterations must be positive")
    if args.objective_map and not Path(args.objective_map).is_file():
        parser.error(f"Objective map not found: {args.objective_map}")

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

    check_required(["PLANNER_MODEL", "CODER_MODEL", "REVIEWER_MODEL"])
    logger.info(
        "Using models - planner: %s, coder: %s, reviewer: %s",
        os.environ.get("PLANNER_MODEL"),
        os.environ.get("CODER_MODEL"),
        os.environ.get("REVIEWER_MODEL"),
    )

    if args.triage:
        logger.info("Running triage for: %s", " ".join(args.triage))
        cmd = ["pytest", "-q", *args.triage]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        output = proc.stdout + proc.stderr
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        triage_log = Path("logs") / f"triage_{timestamp}.log"
        triage_log.parent.mkdir(parents=True, exist_ok=True)
        triage_log.write_text(output, encoding="utf-8")
        if proc.returncode == 0:
            logger.info("Selected tests passed; no triage needed")
            return 0
        from corpus_memory_logging import INTERACTIONS_FILE

        start_lines = 0
        if INTERACTIONS_FILE.exists():
            with INTERACTIONS_FILE.open("r", encoding="utf-8") as fh:
                start_lines = sum(1 for _ in fh)
        tail = "\n".join(output.splitlines()[-20:])
        objective = (
            f"Fix failing tests: {' '.join(args.triage)}\nPytest log tail:\n{tail}"
        )
        run_dev_cycle(objective, repo=Path.cwd(), max_iterations=args.max_iterations)
        if INTERACTIONS_FILE.exists():
            with INTERACTIONS_FILE.open("r", encoding="utf-8") as fh:
                lines = fh.read().splitlines()
            new_lines = lines[start_lines:]
            if new_lines:
                triage_dir = Path("data/triage_sessions")
                triage_dir.mkdir(parents=True, exist_ok=True)
                transcript = triage_dir / f"{timestamp}.jsonl"
                transcript.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
                logger.info("Triage transcript written to %s", transcript)
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
    logger.info("Planner/coder/reviewer cycle begins")

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
    logger.info("Planner/coder/reviewer cycle finished")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
