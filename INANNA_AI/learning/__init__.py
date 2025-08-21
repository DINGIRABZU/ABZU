"""Utilities for fetching external learning data."""

from __future__ import annotations

from . import (github_metadata, github_scraper, project_gutenberg,
               training_guide)

__all__ = [
    "project_gutenberg",
    "github_scraper",
    "training_guide",
    "github_metadata",
]
