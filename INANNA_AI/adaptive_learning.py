from __future__ import annotations

"""Adaptive learning agents for threshold and wording tuning."""

from dataclasses import dataclass, field
from typing import Dict, List
import json
import os
from pathlib import Path

import numpy as np
from stable_baselines3 import PPO
import gymnasium as gym

CONFIG_ENV_VAR = "MIRROR_THRESHOLDS_PATH"
CONFIG_PATH = Path(__file__).resolve().parents[1] / "mirror_thresholds.json"


class _DummyEnv(gym.Env):
    """Minimal environment for PPO training."""

    observation_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(1,), dtype=np.float32)
    action_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(1,), dtype=np.float32)

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

    def update(self, reward: float, new_categories: Dict[str, List[str]] | None = None) -> None:
        self.model.learn(total_timesteps=1)
        self.threshold = float(np.clip(self.threshold + reward * 0.01, 0.0, 1.0))
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

    def update(self, reward: float, new_wording: List[str] | None = None) -> None:
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
        json.dumps({"_comment": "Tolerance per emotion for the reflection loop to trigger self-correction", **values}, indent=2),
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
