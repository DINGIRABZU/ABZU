import logging
from typing import Any, Dict, Tuple

from core.utils.optional_deps import lazy_import

np = lazy_import("numpy")
gym = lazy_import("gymnasium")

logger = logging.getLogger(__name__)

if getattr(np, "__stub__", False) or getattr(gym, "__stub__", False):

    class ContextEnv:  # type: ignore[no-redef]
        """Stub environment when RL dependencies are missing."""

        observation_space = None
        action_space = None

        def __init__(self, *_: Any, **__: Any) -> None:  # pragma: no cover - stub
            logger.warning(
                "gymnasium or numpy not installed; reinforcement learning disabled",
            )

        def reset(
            self, *args: Any, **kwargs: Any
        ) -> Tuple[None, Dict[str, Any]]:  # pragma: no cover - stub
            raise NotImplementedError("reinforcement learning is disabled")

        def step(
            self, *args: Any, **kwargs: Any
        ) -> Tuple[None, float, bool, bool, Dict[str, Any]]:  # pragma: no cover - stub
            raise NotImplementedError("reinforcement learning is disabled")

else:

    class ContextEnv(gym.Env):  # pragma: no cover - minimal RL env
        """Minimal environment for context-based reinforcement learning."""

        metadata = {"render.modes": []}

        def __init__(self) -> None:
            self.observation_space = gym.spaces.Box(
                low=0.0,
                high=1.0,
                shape=(4,),
                dtype=np.float32,
            )
            self.action_space = gym.spaces.Discrete(2)
            self._state = np.zeros(4, dtype=np.float32)

        def reset(
            self,
            *,
            seed: int | None = None,
            options: Dict[str, Any] | None = None,
        ) -> Tuple[Any, Dict[str, Any]]:
            super().reset(seed=seed)
            self._state = np.zeros(4, dtype=np.float32)
            return self._state.copy(), {}

        def step(self, action: int) -> Tuple[Any, float, bool, bool, Dict[str, Any]]:
            reward = float(action == 1)
            terminated = True
            truncated = False
            self._state = np.random.random(4).astype(np.float32)
            return self._state.copy(), reward, terminated, truncated, {}


__all__ = ["ContextEnv"]
