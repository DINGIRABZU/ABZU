"""High-level orchestrator selecting agents and wiring memory stores."""

from __future__ import annotations

import logging
from pathlib import Path
from queue import Queue
from typing import Any, Dict, List

from memory import spiral_cortex


AGENT_LOOKUP: Dict[str, str] = {
    "strategic_simulator": "agents.demiurge.strategic_simulator",
    "fast_inference_agent": "agents.shalltear.fast_inference_agent",
    "prompt_arbiter": "agents.cocytus.prompt_arbiter",
    "aura_capture": "agents.ecosystem.aura_capture",
    "mare_gardener": "agents.ecosystem.mare_gardener",
    "compassion_module": "agents.sebas.compassion_module",
    "security_canary": "agents.victim.security_canary",
    "persona_emulator": "agents.pandora.persona_emulator",
    "vanna_data": "agents.vanna_data",
    "bana": "agents.bana",
    "asiangen": "agents.asiangen",
    "landgraph": "agents.landgraph",
}


class AlbedoOrchestrator:
    """Coordinate planner, coder and reviewer agents for an objective.

    The orchestrator loads memory stores, selects the agent implementations and
    schedules execution. Each invocation records a summary to
    :mod:`memory.spiral_cortex` for later inspection.
    """

    def __init__(
        self,
        *,
        repo: str | Path | None = None,
        max_iterations: int | None = None,
    ) -> None:
        self.repo = Path(repo) if repo is not None else None
        self.max_iterations = max_iterations

    def start(self, objective: str) -> Dict[str, Any]:
        """Run the development cycle for ``objective``.

        Returns a dictionary with planning results, execution details and test
        outcomes.
        """

        from tools import dev_orchestrator as _tools

        queue: Queue[str] = Queue()

        launch_agents_from_config()

        planner_glm = _tools._glm_from_env("PLANNER_MODEL")
        coder_glm = _tools._glm_from_env("CODER_MODEL")
        reviewer_glm = _tools._glm_from_env("REVIEWER_MODEL")

        planner = _tools.Planner(
            "planner", "Plan development tasks", planner_glm, objective, queue
        )
        coder = _tools.Coder("coder", "Write code", coder_glm, objective, queue)
        reviewer = _tools.Reviewer(
            "reviewer", "Review code", reviewer_glm, objective, queue
        )

        logger = logging.getLogger(__name__)
        plan_steps = planner.plan()
        results: List[Dict[str, str]] = []
        iterations = 0
        while not queue.empty():
            if self.max_iterations is not None and iterations >= self.max_iterations:
                break
            task = queue.get()
            logger.info("Executing task %s", task)
            code = coder.code(task)
            review = reviewer.review(task, code)
            results.append({"task": task, "code": code, "review": review})
            iterations += 1

        if not queue.empty():
            logger.info("Max iterations reached with %s tasks remaining", queue.qsize())

        test_result: Dict[str, Any] | None = None
        if self.repo is not None:
            test_result = _tools._run_tests(self.repo)
            if test_result["returncode"] == 0:
                _tools._commit(self.repo, f"Auto commit: {objective}")

        spiral_cortex.log_insight(
            objective,
            [{"plan": plan_steps, "results": len(results)}],
            sentiment=0.0,
        )

        return {
            "objective": objective,
            "plan": plan_steps,
            "results": results,
            "tests": test_result,
        }


def launch_agents_from_config(config_path: Path | None = None) -> Dict[str, bool]:
    """Launch optional agents based on a YAML configuration."""

    import importlib

    logger = logging.getLogger(__name__)
    launched: Dict[str, bool] = {}

    if config_path is None:
        config_path = Path(__file__).with_name("pipeline") / "agents.yaml"

    if not Path(config_path).exists():
        return launched

    try:
        import yaml
    except Exception:  # pragma: no cover - yaml is optional
        logger.warning("PyYAML not installed; skipping optional agents")
        return launched

    with open(config_path, "r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh) or {}

    for name, settings in config.items():
        if not isinstance(settings, dict) or not settings.get("enabled"):
            continue
        module_path = AGENT_LOOKUP.get(name)
        if module_path is None:
            logger.warning("Unknown agent %s in configuration", name)
            continue
        try:
            module = importlib.import_module(module_path)
            launch = getattr(module, "launch", None)
            if callable(launch):
                launch()
            launched[name] = True
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Could not launch %s: %s", name, exc)
    return launched


__all__ = [
    "AlbedoOrchestrator",
    "AGENT_LOOKUP",
    "launch_agents_from_config",
]
