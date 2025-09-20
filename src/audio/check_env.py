"""Diagnostic helpers to verify audio dependencies are installed."""

from __future__ import annotations

import argparse
import importlib
import logging
import shutil
from typing import Dict, Iterable, Tuple

logger = logging.getLogger(__name__)

CORE_PACKAGES: Dict[str, str] = {
    "pydub": "pydub",
    "simpleaudio": "simpleaudio",
}

SUPPORT_PACKAGES: Dict[str, str] = {
    "librosa": "librosa",
    "soundfile": "soundfile",
    "opensmile": "opensmile",
    "clap": "clap",
    "rave": "rave",
}

REQUIRED_BINARIES = ["ffmpeg"]


def check_packages(packages: Dict[str, str]) -> Dict[str, Tuple[bool, str]]:
    """Attempt to import each package and return status information."""

    results: Dict[str, Tuple[bool, str]] = {}
    for name, module_name in packages.items():
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, "__version__", "unknown")
            results[name] = (True, str(version))
        except Exception as exc:  # pragma: no cover - diagnostic output
            results[name] = (False, str(exc))
    return results


def check_binaries(binaries: Iterable[str]) -> Dict[str, Tuple[bool, str]]:
    """Return availability information for the requested binaries."""

    results: Dict[str, Tuple[bool, str]] = {}
    for name in binaries:
        path = shutil.which(name)
        if path:
            results[name] = (True, path)
        else:
            results[name] = (False, "not found")
    return results


def validate_audio_stack(
    *, strict: bool = False, log: logging.Logger | None = None
) -> bool:
    """Validate that the realtime audio stack is ready for playback."""

    log = log or logger
    core = check_packages(CORE_PACKAGES)
    binaries = check_binaries(REQUIRED_BINARIES)
    support = check_packages(SUPPORT_PACKAGES)

    missing: list[str] = []
    for name, (ok, info) in {**core, **binaries}.items():
        if not ok:
            missing.append(f"{name} ({info})")

    for name, (ok, info) in support.items():
        if not ok:
            log.warning("Optional audio package %s missing: %s", name, info)

    if missing:
        message = "Missing audio dependencies: " + ", ".join(missing)
        if strict:
            raise RuntimeError(message)
        log.error(message)
        return False

    log.info("Audio stack ready: pydub, simpleaudio and ffmpeg detected")
    return True


def main(argv: list[str] | None = None) -> int:
    """Print the installation status of required audio packages."""

    parser = argparse.ArgumentParser(description="Validate audio environment")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return a non-zero exit code when the core audio stack is incomplete",
    )
    args = parser.parse_args(argv)

    core = check_packages(CORE_PACKAGES)
    binaries = check_binaries(REQUIRED_BINARIES)
    support = check_packages(SUPPORT_PACKAGES)

    def _print_results(results: Dict[str, Tuple[bool, str]]) -> bool:
        ok_all = True
        for name, (ok, info) in results.items():
            if ok:
                print(f"{name}: {info}")
            else:
                ok_all = False
                print(f"{name}: MISSING ({info})")
        return ok_all

    core_ok = _print_results(core)
    binary_ok = _print_results(binaries)
    support_ok = _print_results(support)

    if args.strict and (not core_ok or not binary_ok):
        return 1
    if not (core_ok and binary_ok and support_ok):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
