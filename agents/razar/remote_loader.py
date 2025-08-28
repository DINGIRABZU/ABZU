"""Download and load remote RAZAR agents at runtime.

This utility can pull Python modules from arbitrary HTTP endpoints or Git
repositories and load them with :mod:`importlib`.  It can also interact with
HTTP‑based GPT services such as GLM‑4 through :mod:`requests`.  Remote agents
must expose a standard interface consisting of ``configure()`` and
``patch()`` functions.

``configure()`` should return a dictionary describing runtime parameters while
``patch()`` may return suggestions or diff strings used for self‑repair.  Both
responses are logged to ``logs/razar_remote_agents.json`` for later audit.
"""

from __future__ import annotations

import importlib.util
import json
import logging
from pathlib import Path
import shutil
from types import ModuleType
from typing import Any, Dict, Tuple, Protocol

from datetime import datetime

import requests

try:  # pragma: no cover - optional dependency
    from git import Repo
except Exception:  # pragma: no cover - optional dependency
    Repo = None  # type: ignore

logger = logging.getLogger(__name__)

# Directory to cache downloaded agent modules or repositories
CACHE_DIR = Path(__file__).resolve().parent / "_remote_cache"
# Path to interaction log
LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "razar_remote_agents.json"


class RemoteAgent(Protocol):  # pragma: no cover - typing helper
    """Interface all remote agents must implement.

    ``configure`` should return a mapping of runtime options while ``patch``
    receives an optional context object and may return any value, typically a
    diff string or suggestion structure.
    """

    def configure(self) -> Dict[str, Any]: ...

    def patch(self, context: Any | None = None) -> Any: ...


def _download(url: str, dest: Path) -> None:
    """Download ``url`` into ``dest``."""

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(response.text, encoding="utf-8")


def _clone_repo(repo_url: str, dest: Path, branch: str = "main") -> None:
    """Clone ``repo_url`` into ``dest`` using :mod:`GitPython`."""

    if Repo is None:  # pragma: no cover - optional dependency
        raise ImportError("GitPython is required for cloning repositories")

    Repo.clone_from(repo_url, dest, branch=branch)


def _persist_log(
    name: str, *, config: Dict[str, Any] | None = None, suggestion: Any | None = None
) -> None:
    """Store ``config`` and ``suggestion`` for ``name`` in the audit log."""

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    data: Dict[str, Any] = {}
    if LOG_PATH.exists():
        try:
            data = json.loads(LOG_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning("Could not decode %s; starting fresh", LOG_PATH)

    record: Dict[str, Any] = data.get(name, {})
    if config is not None:
        record["config"] = config
    if suggestion is not None:
        record.setdefault("suggestions", []).append(suggestion)
    record["timestamp"] = datetime.utcnow().isoformat()
    data[name] = record

    LOG_PATH.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def _load_and_log(
    path: Path, name: str, patch_context: Any | None
) -> Tuple[ModuleType, Dict[str, Any], Any]:
    """Import module from ``path`` and execute ``configure()``/``patch()`` hooks."""

    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import agent {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    config: Dict[str, Any] = {}
    suggestion: Any | None = None

    configure = getattr(module, "configure", None)
    if callable(configure):
        try:
            result = configure()
        except Exception as exc:  # pragma: no cover - runtime safeguard
            logger.error("configure() for %s raised %s", name, exc)
        else:
            if isinstance(result, dict):
                config = result
            else:
                logger.warning("configure() for %s did not return a dict", name)
    else:
        logger.warning("Agent %s missing configure() function", name)

    patch = getattr(module, "patch", None)
    if callable(patch):
        try:
            suggestion = patch(patch_context) if patch_context is not None else patch()
        except Exception as exc:  # pragma: no cover - runtime safeguard
            logger.error("patch() for %s raised %s", name, exc)
    else:
        logger.warning("Agent %s missing patch() function", name)

    _persist_log(name, config=config if config else None, suggestion=suggestion)

    return module, config, suggestion


def load_remote_agent(
    name: str, url: str, *, refresh: bool = False, patch_context: Any | None = None
) -> Tuple[ModuleType, Dict[str, Any], Any]:
    """Return the remote agent module, its configuration and patch suggestion.

    Parameters
    ----------
    name:
        Module name for the downloaded agent.
    url:
        HTTP(S) location of the Python source file.
    refresh:
        If ``True``, the module is downloaded even if a cached copy exists.
    patch_context:
        Optional value passed to the agent's ``patch()`` function.
    """

    path = CACHE_DIR / f"{name}.py"
    if refresh or not path.exists():
        logger.info("Downloading agent %s from %s", name, url)
        _download(url, path)

    return _load_and_log(path, name, patch_context)


def load_remote_agent_from_git(
    name: str,
    repo_url: str,
    module_path: str,
    *,
    branch: str = "main",
    refresh: bool = False,
    patch_context: Any | None = None,
) -> Tuple[ModuleType, Dict[str, Any], Any]:
    """Load a remote agent from a Git repository using :mod:`GitPython`.

    Parameters
    ----------
    name:
        Import name for the agent module.
    repo_url:
        URL to the Git repository.
    module_path:
        Path to the Python file within the repository.
    branch:
        Branch to check out. Defaults to ``"main"``.
    refresh:
        If ``True``, reclone the repository even if a cached copy exists.
    patch_context:
        Optional value passed to the agent's ``patch()`` function.
    """

    repo_dir = CACHE_DIR / f"{name}_repo"
    if refresh and repo_dir.exists():
        shutil.rmtree(repo_dir)
    if not repo_dir.exists():
        logger.info("Cloning agent repo %s from %s", name, repo_url)
        _clone_repo(repo_url, repo_dir, branch)

    path = repo_dir / module_path
    if not path.exists():  # pragma: no cover - user error
        raise FileNotFoundError(
            f"Agent module {module_path} not found in repo {repo_url}"
        )

    return _load_and_log(path, name, patch_context)


def load_remote_gpt_agent(
    name: str,
    base_url: str,
    *,
    params: Dict[str, Any] | None = None,
    patch_context: Any | None = None,
) -> Tuple[Dict[str, Any], Any]:
    """Interact with an HTTP‑based GPT agent using :mod:`requests`.

    The endpoint at ``base_url`` must expose ``/configure`` and ``/patch`` routes
    accepting JSON payloads and returning JSON responses.

    Parameters
    ----------
    name:
        Identifier for the agent, used for logging.
    base_url:
        Base URL of the GPT agent service.
    params:
        Optional parameters sent in the ``configure`` request body.
    patch_context:
        Optional value passed to the agent's ``patch`` endpoint.
    """

    config: Dict[str, Any] = {}
    suggestion: Any | None = None

    url = base_url.rstrip("/")

    try:
        response = requests.post(f"{url}/configure", json=params or {}, timeout=30)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            config = data
        else:  # pragma: no cover - defensive
            logger.warning("configure() for %s did not return a JSON object", name)
    except Exception as exc:  # pragma: no cover - runtime safeguard
        logger.error("configure() request for %s failed: %s", name, exc)

    try:
        payload = {"context": patch_context} if patch_context is not None else {}
        response = requests.post(f"{url}/patch", json=payload, timeout=60)
        response.raise_for_status()
        suggestion = response.json()
    except Exception as exc:  # pragma: no cover - runtime safeguard
        logger.error("patch() request for %s failed: %s", name, exc)

    _persist_log(name, config=config if config else None, suggestion=suggestion)

    return config, suggestion
