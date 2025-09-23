"""Lightweight server stubs for communication.gateway tests."""

from __future__ import annotations

import asyncio


async def generate_video(_content: str) -> None:
    return None


async def broadcast_avatar_update(_content: str) -> None:
    return None


async def list_styles() -> list[str]:
    await asyncio.sleep(0)
    return []
