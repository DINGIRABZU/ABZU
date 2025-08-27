from __future__ import annotations

"""Avatar selection hooks driven by YOLOE detections."""

from typing import Iterable, Mapping

from vision.yoloe_adapter import Detection

# Mapping of object labels to avatar texture paths
AVATAR_MAP: Mapping[str, str] = {
    "cat": "avatars/cat.png",
    "dog": "avatars/dog.png",
}

DEFAULT_AVATAR = "avatars/default.png"

_current_avatar = DEFAULT_AVATAR


def consume_detections(detections: Iterable[Detection]) -> str:
    """Update current avatar based on YOLOE ``detections``.

    Parameters
    ----------
    detections:
        Iterable of :class:`~vision.yoloe_adapter.Detection` objects.

    Returns
    -------
    str
        Path to the selected avatar texture.
    """

    global _current_avatar
    for det in detections:
        label = det.label.lower()
        if label in AVATAR_MAP:
            _current_avatar = AVATAR_MAP[label]
            break
    else:
        _current_avatar = DEFAULT_AVATAR
    return _current_avatar


def current_avatar() -> str:
    """Return the most recently selected avatar texture."""

    return _current_avatar


__all__ = ["consume_detections", "current_avatar", "AVATAR_MAP", "DEFAULT_AVATAR"]
