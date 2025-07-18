from __future__ import annotations

"""Initialize the Crown agent by loading configuration and memory."""

import logging
import os
from pathlib import Path

import yaml

from INANNA_AI.glm_integration import GLMIntegration
from INANNA_AI import glm_integration as gi
import vector_memory
from INANNA_AI import corpus_memory
import servant_model_manager as smm
try:  # pragma: no cover - optional dependency
    import requests
except Exception:  # pragma: no cover - optional dependency
    requests = None  # type: ignore

logger = logging.getLogger(__name__)

CONFIG_FILE = Path(__file__).resolve().parent / "config" / "INANNA_CORE.yaml"


def _load_config() -> dict:
    """Return configuration merged with environment overrides."""
    cfg: dict = {}
    if CONFIG_FILE.exists():
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}

    env_map = {
        "glm_api_url": "GLM_API_URL",
        "glm_api_key": "GLM_API_KEY",
        "model_path": "MODEL_PATH",
        "memory_dir": "MEMORY_DIR",
    }
    for key, env in env_map.items():
        val = os.getenv(env)
        if val:
            cfg[key] = val
            logger.info("%s loaded from env %s", key, env)

    servant = cfg.get("servant_models", {})
    for name, env in (
        ("deepseek", "DEEPSEEK_URL"),
        ("mistral", "MISTRAL_URL"),
        ("kimi_k2", "KIMI_K2_URL"),
    ):
        val = os.getenv(env)
        if val:
            servant[name] = val
            logger.info("servant %s url loaded from env %s", name, env)
    if servant:
        cfg["servant_models"] = servant

    return cfg


def _init_memory(cfg: dict) -> None:
    mem_dir = cfg.get("memory_dir")
    if mem_dir:
        mem_dir = Path(mem_dir)
        vec_path = mem_dir / "vector_memory"
        corpus_path = mem_dir / "chroma"
        vec_path.mkdir(parents=True, exist_ok=True)
        corpus_path.mkdir(parents=True, exist_ok=True)
        logger.info("memory directories created: %s, %s", vec_path, corpus_path)

        os.environ["VECTOR_DB_PATH"] = str(vec_path)
        logger.info("initializing vector memory at %s", vec_path)
        try:
            vector_memory._get_collection()
            logger.info("Vector memory loaded from %s", vec_path)
        except Exception as exc:  # pragma: no cover - optional deps
            logger.warning("Vector memory unavailable: %s", exc)

        corpus_memory.CHROMA_DIR = corpus_path
        logger.info("initializing corpus memory at %s", corpus_path)
        try:
            corpus_memory.create_collection(dir_path=corpus_memory.CHROMA_DIR)
            logger.info("Corpus memory loaded from %s", corpus_path)
        except Exception as exc:  # pragma: no cover - optional deps
            logger.warning("Corpus memory unavailable: %s", exc)


def _check_glm(integration: GLMIntegration) -> None:
    try:
        resp = integration.complete("ping")
    except Exception as exc:  # pragma: no cover - network errors
        logger.error("Failed to reach GLM endpoint: %s", exc)
        raise RuntimeError("GLM endpoint unavailable") from exc
    logger.info("GLM test response: %s", resp)
    if resp == gi.SAFE_ERROR_MESSAGE:
        raise RuntimeError("GLM endpoint returned error")


def _register_http_servant(name: str, url: str) -> None:
    def _invoke(prompt: str) -> str:
        if requests is None:
            return ""
        try:
            resp = requests.post(url, json={"prompt": prompt}, timeout=10)
            resp.raise_for_status()
            try:
                return resp.json().get("text", "")
            except Exception:
                return resp.text
        except Exception as exc:  # pragma: no cover - network errors
            logger.error("Servant %s failed: %s", name, exc)
            return ""

    smm.register_model(name, _invoke)


def _init_servants(cfg: dict) -> None:
    servants = dict(cfg.get("servant_models") or {})
    kimi_url = servants.pop("kimi_k2", None) or os.getenv("KIMI_K2_URL")
    if kimi_url:
        os.environ.setdefault("KIMI_K2_URL", kimi_url)
        smm.register_kimi_k2()
    for name, url in servants.items():
        _register_http_servant(name, url)


def initialize_crown() -> GLMIntegration:
    """Return a :class:`GLMIntegration` instance configured from YAML."""
    cfg = _load_config()
    integration = GLMIntegration(
        endpoint=cfg.get("glm_api_url"),
        api_key=cfg.get("glm_api_key"),
    )
    if cfg.get("model_path"):
        os.environ.setdefault("MODEL_PATH", str(cfg["model_path"]))
    _init_memory(cfg)
    _init_servants(cfg)
    try:
        _check_glm(integration)
    except RuntimeError as exc:
        logger.error("%s", exc)
        raise SystemExit(1)
    return integration


__all__ = ["initialize_crown"]
