"""Simple neural style transfer utilities."""

from __future__ import annotations

from typing import Iterable

import numpy as np


def blend_frame_with_embedding(
    base_frame: np.ndarray, style_embedding: np.ndarray, alpha: float = 0.6
) -> np.ndarray:
    """Blend ``base_frame`` with ``style_embedding``.

    Parameters
    ----------
    base_frame:
        Frame to stylise.
    style_embedding:
        Style representation broadcastable to ``base_frame``.
    alpha:
        Blend factor in ``[0, 1]`` where higher values favour the style.

    Returns
    -------
    np.ndarray
        Stylised frame with the same dtype as ``base_frame``.
    """
    if base_frame.shape != style_embedding.shape:
        style_embedding = np.broadcast_to(style_embedding, base_frame.shape)
    blended = (1 - alpha) * base_frame + alpha * style_embedding
    return blended.astype(base_frame.dtype)


def apply_style_transfer(
    frames: Iterable[np.ndarray], style_embedding: np.ndarray, alpha: float = 0.6
) -> list[np.ndarray]:
    """Apply style transfer to an iterable of frames."""
    return [blend_frame_with_embedding(f, style_embedding, alpha) for f in frames]
