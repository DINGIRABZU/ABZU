from __future__ import annotations

"""Credential rotation helper for remote RAZAR agents.

This script reads rotation metadata stored under ``secrets/`` (JSON or YAML
documents), generates placeholder tokens for each configured remote agent, and
verifies that :mod:`razar.ai_invoker` reloads credentials after
``invalidate_agent_config_cache`` is called.

The rotation metadata should contain entries with at least the agent ``name``
and an optional ``env`` key describing the environment variable that will hold
the refreshed credential. ``config_path`` can override the default
``config/razar_ai_agents.json`` file on a per-agent basis. Example::

    agents:
      - name: demo_agent
        env: DEMO_AGENT_TOKEN
        config_path: ./config/razar_ai_agents.json

The helper never persists the placeholders to disk when executed with
``--dry-run``; instead it writes temporary copies of the configuration to
validate that cache invalidation behaves correctly. When run without
``--dry-run`` (or through :func:`rotate_remote_agent_keys` with
``dry_run=False``) the helper updates the referenced configuration files in
place.
"""

from dataclasses import dataclass
import argparse
import contextlib
import json
import logging
import os
from pathlib import Path
import tempfile
from typing import Any, Iterable, Mapping, Sequence

try:  # pragma: no cover - optional dependency guard
    import yaml
except Exception:  # pragma: no cover - optional dependency guard
    yaml = None  # type: ignore[assignment]

from razar import ai_invoker

LOGGER = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = ai_invoker.AGENT_CONFIG_PATH


class RotationError(RuntimeError):
    """Raised when credential rotation metadata cannot be applied."""


@dataclass(frozen=True)
class RotationSpec:
    """Rotation metadata for a single remote agent."""

    name: str
    env_var: str | None
    config_path: Path
    source: Path
    raw: Mapping[str, Any]

    @property
    def normalized_name(self) -> str:
        return self.name.lower()


@dataclass(frozen=True)
class RotationResult:
    """Outcome of applying a placeholder token for an agent."""

    spec: RotationSpec
    placeholder: str
    previous_token: str | None
    config_path: Path
    env_var: str | None
    applied: bool


def _load_metadata_file(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise RotationError(
                f"pyyaml is required to parse {path}, install it before rotating"
            )
        try:
            return yaml.safe_load(text) or {}
        except yaml.YAMLError as exc:  # type: ignore[attr-defined]
            raise RotationError(f"failed to parse YAML metadata {path}: {exc}")
    try:
        return json.loads(text or "{}")
    except json.JSONDecodeError as exc:
        raise RotationError(f"failed to parse JSON metadata {path}: {exc}")


def _iter_agent_entries(payload: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(payload, Mapping):
        if "agents" in payload and isinstance(payload["agents"], Sequence):
            yield from (item for item in payload["agents"] if isinstance(item, Mapping))
            return
        if "rotation" in payload and isinstance(payload["rotation"], Sequence):
            yield from (
                item for item in payload["rotation"] if isinstance(item, Mapping)
            )
            return
        yield payload
        return
    if isinstance(payload, Sequence):
        yield from (item for item in payload if isinstance(item, Mapping))


def _resolve_config_path(candidate: str | None, source: Path) -> Path:
    if not candidate:
        return DEFAULT_CONFIG_PATH
    path = Path(candidate)
    if not path.is_absolute():
        path = (source.parent / path).resolve()
        if not path.exists():
            path = (REPO_ROOT / candidate).resolve()
    return path


def _normalize_env_name(name: str | None, fallback: str | None) -> str | None:
    value = (name or "").strip()
    if value:
        return value
    return fallback


def load_rotation_metadata(
    secrets_dir: Path | str = REPO_ROOT / "secrets",
    *,
    default_config: Path | None = None,
) -> list[RotationSpec]:
    """Return rotation specifications discovered under ``secrets_dir``."""

    base = Path(secrets_dir).expanduser()
    if not base.exists():
        raise RotationError(f"rotation directory {base} does not exist")
    if not base.is_dir():
        raise RotationError(f"rotation path {base} is not a directory")

    specs: list[RotationSpec] = []
    for path in sorted(base.rglob("*")):
        if path.suffix.lower() not in {".json", ".yaml", ".yml"}:
            continue
        payload = _load_metadata_file(path)
        for entry in _iter_agent_entries(payload):
            name = entry.get("name")
            if not isinstance(name, str) or not name.strip():
                LOGGER.debug("Skipping metadata without agent name in %s", path)
                continue
            env_var = (
                entry.get("env") or entry.get("env_var") or entry.get("environment")
            )
            fallback_env = ai_invoker._MANDATORY_AGENT_ENV_VARS.get(name.lower())
            normalized_env = _normalize_env_name(env_var, fallback_env)
            config_override = entry.get("config_path") or entry.get("config")
            config_path = (
                Path(default_config)
                if default_config is not None
                else DEFAULT_CONFIG_PATH
            )
            if config_override:
                config_path = _resolve_config_path(str(config_override), path)
            specs.append(
                RotationSpec(
                    name=name.strip(),
                    env_var=normalized_env,
                    config_path=config_path,
                    source=path,
                    raw=entry,
                )
            )
    return specs


def _sanitize_placeholder_seed(value: str) -> str:
    cleaned = [ch if ch.isalnum() else "_" for ch in value.upper()]
    result = "".join(cleaned).strip("_")
    return result or "AGENT"


def generate_placeholders(
    specs: Iterable[RotationSpec],
    *,
    prefix: str = "ROTATE",
    suffix: str = "TOKEN",
) -> dict[str, str]:
    """Return placeholder tokens keyed by normalized agent name."""

    placeholders: dict[str, str] = {}
    for spec in specs:
        seed = spec.env_var or spec.name
        sanitized = _sanitize_placeholder_seed(seed)
        parts = [prefix.strip().upper(), sanitized]
        if suffix:
            parts.append(suffix.strip().upper())
        placeholder = "_".join(part for part in parts if part)
        placeholders[spec.normalized_name] = placeholder
    return placeholders


@contextlib.contextmanager
def _temporary_env(updates: Mapping[str, str]):
    previous: dict[str, str | None] = {}
    try:
        for key, value in updates.items():
            previous[key] = os.environ.get(key)
            os.environ[key] = value
        yield
    finally:
        for key, original in previous.items():
            if original is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original


def _load_config(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RotationError(f"agent config {path} is missing") from exc
    except json.JSONDecodeError as exc:
        raise RotationError(f"agent config {path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise RotationError(f"agent config {path} must contain a JSON object")
    return data


def _write_config(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def _update_agent_entry(
    data: Mapping[str, Any],
    *,
    agent_name: str,
    placeholder: str,
) -> tuple[dict[str, Any], str | None]:
    payload = dict(data)
    agents = payload.get("agents")
    if not isinstance(agents, list):
        raise RotationError("agent configuration missing 'agents' list")
    updated_agents: list[dict[str, Any]] = []
    previous_token: str | None = None
    target_lower = agent_name.lower()
    found = False
    for entry in agents:
        if not isinstance(entry, dict):
            updated_agents.append(entry)
            continue
        name = entry.get("name")
        if isinstance(name, str) and name.lower() == target_lower:
            found = True
            normalized_entry = dict(entry)
            auth = normalized_entry.get("auth")
            if not isinstance(auth, dict):
                auth = {}
            token_field = None
            for candidate in ("token", "key", "secret"):
                value = auth.get(candidate)
                if isinstance(value, str):
                    token_field = candidate
                    previous_token = value
                    break
            if token_field is None:
                token_field = "token"
            if previous_token == placeholder:
                raise RotationError(
                    f"placeholder for {agent_name} matches existing credential"
                )
            auth[token_field] = placeholder
            normalized_entry["auth"] = auth
            updated_agents.append(normalized_entry)
        else:
            updated_agents.append(entry)
    if not found:
        raise RotationError(f"agent {agent_name} not present in configuration")
    payload["agents"] = updated_agents
    return payload, previous_token


def _verify_reload(
    path: Path,
    *,
    spec: RotationSpec,
    placeholder: str,
    dry_run: bool,
) -> None:
    target_path = path
    env_updates = {spec.env_var: placeholder} if spec.env_var else {}
    with _temporary_env(env_updates):
        try:
            ai_invoker.invalidate_agent_config_cache(target_path)
            _active, definitions = ai_invoker.load_agent_definitions(target_path)
        except Exception as exc:  # pragma: no cover - defensive guard
            message = f"failed to load agent definitions for {spec.name}"
            raise RotationError(message) from exc
        match = next(
            (
                entry
                for entry in definitions
                if entry.normalized == spec.normalized_name
            ),
            None,
        )
        if match is None:
            raise RotationError(
                f"agent {spec.name} missing after cache refresh using {target_path}"
            )
        if match.token != placeholder:
            message = (
                "agent {name} did not reload placeholder credential after "
                "invalidation"
            ).format(name=spec.name)
            raise RotationError(message)
    if dry_run:
        try:
            target_path.unlink()
        except FileNotFoundError:
            pass


def rotate_remote_agent_keys(
    *,
    secrets_dir: Path | str = REPO_ROOT / "secrets",
    default_config: Path | None = None,
    prefix: str = "ROTATE",
    suffix: str = "TOKEN",
    dry_run: bool = True,
) -> list[RotationResult]:
    """Apply rotation metadata and verify cache invalidation."""

    specs = load_rotation_metadata(secrets_dir, default_config=default_config)
    if not specs:
        raise RotationError(f"no rotation metadata discovered under {secrets_dir}")
    placeholders = generate_placeholders(specs, prefix=prefix, suffix=suffix)
    results: list[RotationResult] = []
    for spec in specs:
        config = _load_config(spec.config_path)
        updated_config, previous_token = _update_agent_entry(
            config, agent_name=spec.name, placeholder=placeholders[spec.normalized_name]
        )
        if dry_run:
            fd, tmp_name = tempfile.mkstemp(prefix="razar_rotation_", suffix=".json")
            os.close(fd)
            tmp_file = Path(tmp_name)
            _write_config(tmp_file, updated_config)
            verify_path = tmp_file
        else:
            _write_config(spec.config_path, updated_config)
            verify_path = spec.config_path
        _verify_reload(
            verify_path,
            spec=spec,
            placeholder=placeholders[spec.normalized_name],
            dry_run=dry_run,
        )
        results.append(
            RotationResult(
                spec=spec,
                placeholder=placeholders[spec.normalized_name],
                previous_token=previous_token,
                config_path=spec.config_path,
                env_var=spec.env_var,
                applied=not dry_run,
            )
        )
    return results


def _format_result(result: RotationResult) -> str:
    env_part = f" env={result.env_var}" if result.env_var else ""
    action = "applied" if result.applied else "validated"
    return (
        f"{result.spec.name} -> {result.placeholder}{env_part} "
        f"({action} using {result.config_path})"
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--secrets-dir",
        default=str(REPO_ROOT / "secrets"),
        help="directory containing rotation metadata (default: %(default)s)",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="override default config path for metadata lacking explicit config_path",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "write updates to the referenced config files instead of dry-run "
            "validation"
        ),
    )
    parser.add_argument(
        "--prefix",
        default="ROTATE",
        help="placeholder prefix (default: %(default)s)",
    )
    parser.add_argument(
        "--suffix",
        default="TOKEN",
        help="placeholder suffix (default: %(default)s)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="enable debug logging",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    try:
        results = rotate_remote_agent_keys(
            secrets_dir=args.secrets_dir,
            default_config=Path(args.config).expanduser() if args.config else None,
            prefix=args.prefix,
            suffix=args.suffix,
            dry_run=not args.apply,
        )
    except RotationError as exc:
        LOGGER.error("rotation failed: %s", exc)
        return 1

    for result in results:
        LOGGER.info(_format_result(result))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
