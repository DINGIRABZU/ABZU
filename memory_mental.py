from __future__ import annotations

"""Neo4j-backed task memory with optional reinforcement learning hooks."""

from dataclasses import dataclass
import json
import logging
from datetime import datetime
from typing import Any, Dict, List

try:  # pragma: no cover - optional dependency
    from neo4j import Driver, GraphDatabase
except Exception:  # pragma: no cover - optional dependency
    GraphDatabase = None  # type: ignore
    Driver = object  # type: ignore

from config import settings
from aspect_processor import (
    analyze_geometric,
    analyze_phonetic,
    analyze_semantic,
    analyze_temporal,
)

try:  # pragma: no cover - optional dependencies
    import numpy as np
    import gymnasium as gym
    from stable_baselines3 import DQN
except Exception:  # pragma: no cover - optional dependencies
    np = None  # type: ignore
    gym = None  # type: ignore
    DQN = None  # type: ignore


logger = logging.getLogger(__name__)

_DRIVER: Driver | None = None
_RL_MODEL: DQN | None = None


@dataclass
class Task:
    """Task node schema."""

    id: str
    description: str | None = None


@dataclass
class Context:
    """Context node schema."""

    data: Dict[str, Any]


@dataclass
class Decision:
    """Decision node schema."""

    result: str
    reward: float = 0.0


REL_HAS_CONTEXT = "HAS_CONTEXT"
REL_CAUSED = "CAUSED"
REL_FOLLOWS = "FOLLOWS"


def _get_driver() -> Driver:
    """Return a cached Neo4j driver."""

    global _DRIVER
    if _DRIVER is None:
        if GraphDatabase is None:  # pragma: no cover - dependency missing
            raise RuntimeError("neo4j driver not installed")
        _DRIVER = GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )
    return _DRIVER


if gym is not None and np is not None:

    class _ContextEnv(gym.Env):  # pragma: no cover - simple RL environment
        """Minimal environment for context-based reinforcement learning."""

        def __init__(self) -> None:
            self.observation_space = gym.spaces.Box(
                -np.inf, np.inf, (1,), dtype=float
            )
            self.action_space = gym.spaces.Discrete(1)

        def reset(
            self,
            *,
            seed: int | None = None,
            options: Dict[str, Any] | None = None,
        ):
            return np.zeros(1, dtype=float), {}

        def step(self, action: int):
            return np.zeros(1, dtype=float), 0.0, True, False, {}

else:  # pragma: no cover - dependencies missing

    class _ContextEnv:  # type: ignore[no-redef]
        pass


def init_rl_model() -> None:
    """Initialise the reinforcement learning model if dependencies exist."""

    global _RL_MODEL
    if DQN is None or gym is None or np is None:
        logger.info("stable-baselines3 or gymnasium not installed; RL disabled")
        return
    if _RL_MODEL is None:
        env = _ContextEnv()
        _RL_MODEL = DQN("MlpPolicy", env, verbose=0)


def _update_rl(context: Dict[str, Any], reward: float) -> None:
    """Update RL model with a new experience."""

    if _RL_MODEL is None or np is None:
        return
    obs = np.array([float(len(context))])
    _RL_MODEL.replay_buffer.add(
        obs,
        obs,
        np.array([0]),
        np.array([reward]),
        np.array([False]),
        [{}],
    )
    _RL_MODEL.train(batch_size=1, gradient_steps=1)


def record_task_flow(task_id: str, context: Dict[str, Any], reward: float = 0.0) -> None:
    """Record a task execution and optionally update the RL model."""

    analyze_phonetic(task_id)
    analyze_semantic(json.dumps(context))
    analyze_geometric(context)
    analyze_temporal(datetime.utcnow().isoformat())
    ctx = json.dumps(context)
    driver = _get_driver()
    with driver.session() as session:
        session.execute_write(
            lambda tx: tx.run(
                """
                MERGE (t:Task {id: $task_id})
                CREATE (c:Context {data: $ctx})
                MERGE (t)-[:HAS_CONTEXT]->(c)
                """,
                task_id=task_id,
                ctx=ctx,
            )
        )
    _update_rl(context, reward)


def query_related_tasks(task_id: str) -> List[str]:
    """Return task IDs that share context with ``task_id``."""

    driver = _get_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (t:Task {id: $task_id})-[:HAS_CONTEXT]->(c)<-[:HAS_CONTEXT]-(o:Task)
            RETURN DISTINCT o.id AS id
            """,
            task_id=task_id,
        )
        return [r["id"] for r in result]


__all__ = [
    "Task",
    "Context",
    "Decision",
    "REL_HAS_CONTEXT",
    "REL_CAUSED",
    "REL_FOLLOWS",
    "init_rl_model",
    "record_task_flow",
    "query_related_tasks",
]
