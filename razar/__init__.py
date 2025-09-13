"""Razar package hosting boot orchestration utilities."""

from pathlib import Path

__version__ = "0.2.3"

# Path to the minimal boot configuration used in tests
BOOT_CONFIG_PATH = Path(__file__).with_name("boot_config.json")

__all__ = ["BOOT_CONFIG_PATH"]
