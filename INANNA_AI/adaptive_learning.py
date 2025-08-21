from __future__ import annotations

"""Adaptive learning agents for threshold and wording tuning."""

import json
import os
import random as _random
import types
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

try:  # pragma: no cover - import side effects
    import numpy as np
except Exception:  # pragma: no cover - allow stubbing in tests

    def _zeros(shape, dtype=float):
        size = shape[0] if isinstance(shape, tuple) else int(shape)
        return [dtype(0)] * size

    def _clip(x, a, b):
        if isinstance(x, (list, tuple)):
            return [max(a, min(b, v)) for v in x]
        return max(a, min(b, x))

    def _rand(size: int | None = None):
        if size is None:
            return _random.random()
        return [_random.random() for _ in range(size)]

    def _randint(low: int, high: int | None = None, size: int | None = None):
        if high is None:
            high = low
            low = 0

        def _one():
            return _random.randint(low, high - 1)

        if size is None:
            return _one()
        return [_one() for _ in range(size)]

    def _permutation(x):
        arr = list(range(x)) if isinstance(x, int) else list(x)
        _random.shuffle(arr)
        return arr

    def _seed(seed: int | None = None):
        _random.seed(seed)

    _rng = types.SimpleNamespace(
        rand=_rand,
        random=_rand,
        randint=_randint,
        permutation=_permutation,
        seed=_seed,
    )

    np = types.SimpleNamespace(
        float32=float,
        zeros=_zeros,
        clip=_clip,
        random=_rng,
    )  # type: ignore

try:  # pragma: no cover - import side effects
    from stable_baselines3 import PPO as _PPO

    if isinstance(np, types.SimpleNamespace):
        raise ImportError("NumPy stub in use")
    PPO = _PPO
except ImportError:  # pragma: no cover - allow stubbing in tests

    class PPO:  # type: ignore
        def __init__(self, *a, **k):
            pass

        def learn(self, *a, **k):
            pass


try:  # pragma: no cover - import side effects
    import gymnasium as gym
except ImportError:  # pragma: no cover - allow stubbing in tests

    class _Box:
        def __init__(self, *a, **k):
            pass

    class _Env:
        pass

    class _Spaces(types.SimpleNamespace):
        Box = _Box

    gym = types.SimpleNamespace(Env=_Env, spaces=_Spaces())  # type: ignore

CONFIG_ENV_VAR = "MIRROR_THRESHOLDS_PATH"
CONFIG_PATH = Path(__file__).resolve().parents[1] / "mirror_thresholds.json"


class _DummyEnv(gym.Env):
    """Minimal environment for PPO training."""

    observation_space = gym.spaces.Box(
        low=-1.0,
        high=1.0,
        shape=(1,),
        dtype=np.float32,
    )
    action_space = gym.spaces.Box(
        low=-1.0,
        high=1.0,
        shape=(1,),
        dtype=np.float32,
    )

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        return np.zeros(1, dtype=np.float32), {}

    def step(self, action):  # pragma: no cover - deterministic output
        return np.zeros(1, dtype=np.float32), 0.0, True, False, {}


@dataclass
class ThresholdAgent:
    """PPO agent managing validator threshold and categories."""

    threshold: float = 0.7
    categories: Dict[str, List[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.env = _DummyEnv()
        self.model = PPO("MlpPolicy", self.env, verbose=0)

    def update(
        self, reward: float, new_categories: Dict[str, List[str]] | None = None
    ) -> None:
        self.model.learn(total_timesteps=1)
        clip_val = np.clip(self.threshold + reward * 0.01, 0.0, 1.0)
        self.threshold = float(clip_val)
        if new_categories:
            for cat, phrases in new_categories.items():
                self.categories.setdefault(cat, []).extend(phrases)


@dataclass
class WordingAgent:
    """PPO agent adjusting reflector wording choices."""

    wording: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.env = _DummyEnv()
        self.model = PPO("MlpPolicy", self.env, verbose=0)

    def update(
        self,
        reward: float,
        new_wording: List[str] | None = None,
    ) -> None:
        self.model.learn(total_timesteps=1)
        if new_wording:
            self.wording = new_wording


THRESHOLD_AGENT = ThresholdAgent()
WORDING_AGENT = WordingAgent()


def _threshold_path() -> Path:
    path_str = os.getenv(CONFIG_ENV_VAR)
    return Path(path_str) if path_str else CONFIG_PATH


def _load_thresholds() -> Dict[str, float]:
    path = _threshold_path()
    if not path.exists():
        return {"default": 0.0}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"default": 0.0}
    data.pop("_comment", None)
    return {k: float(v) for k, v in data.items()}


def _save_thresholds(values: Dict[str, float]) -> None:
    path = _threshold_path()
    path.write_text(
        json.dumps(
            {
                "_comment": (
                    "Tolerance per emotion for the reflection loop to trigger "
                    "self-correction"
                ),
                **values,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


@dataclass
class MirrorThresholdAgent:
    """PPO agent adapting mirror threshold values."""

    thresholds: Dict[str, float] = field(default_factory=_load_thresholds)

    def __post_init__(self) -> None:
        self.env = _DummyEnv()
        self.model = PPO("MlpPolicy", self.env, verbose=0)

    def update(self, reward: float) -> None:
        self.model.learn(total_timesteps=1)
        delta = reward * 0.01
        for emotion, value in self.thresholds.items():
            self.thresholds[emotion] = float(np.clip(value + delta, 0.0, 1.0))
        _save_thresholds(self.thresholds)


MIRROR_THRESHOLD_AGENT = MirrorThresholdAgent()


def update(
    *,
    validator_reward: float | None = None,
    validator_categories: Dict[str, List[str]] | None = None,
    reflector_reward: float | None = None,
    reflector_wording: List[str] | None = None,
) -> None:
    """Update agents with optional feedback."""

    if validator_reward is not None or validator_categories is not None:
        THRESHOLD_AGENT.update(validator_reward or 0.0, validator_categories)
    if reflector_reward is not None or reflector_wording is not None:
        WORDING_AGENT.update(reflector_reward or 0.0, reflector_wording)


def update_mirror_thresholds(reward: float) -> None:
    """Learn one step and update mirror thresholds."""

    MIRROR_THRESHOLD_AGENT.update(reward)
