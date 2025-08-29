from __future__ import annotations

__version__ = "0.1.0"

"""Stream YOLOE detections into RAZAR's planning engine.

The adapter connects the vision system provided by
``vision.yoloe_adapter`` with RAZAR's planning utilities.  Each frame is
processed by :class:`~vision.yoloe_adapter.YOLOEAdapter` and the resulting
:class:`~vision.yoloe_adapter.Detection` objects are used in two ways:

* Avatar or other environment dependent modules are notified so they can
  adjust their behaviour immediately.
* Detected labels are mapped to components managed by the planning engine.
  When a relevant label is seen, the planning engine is invoked and the
  plan entries for the affected components are returned.  Callers may use
  this information to trigger module regeneration.

The class is intentionally lightweight and purely synchronous which keeps
unit tests fast while exercising the integration points between vision and
planning.
"""

from typing import Callable, Dict, Iterable, Mapping

from vision.yoloe_adapter import Detection, YOLOEAdapter
from agents.albedo import vision as avatar_vision
from . import planning_engine

# Mapping from detection labels to plan component names.  In real usage this
# would be populated with environment specific mappings.  A default entry is
# provided so the adapter is functional in minimal test scenarios where the
# fallback YOLOE detector emits the label ``"object"``.
DEFAULT_MODULE_MAP: Mapping[str, str] = {"object": "vision_adapter"}


class VisionAdapter:
    """Bridge YOLOE detections to the planning engine."""

    def __init__(
        self,
        module_map: Mapping[str, str] | None = None,
        planner: Callable[[], Dict[str, Mapping[str, object]]] | None = None,
    ) -> None:
        self.yolo = YOLOEAdapter()
        self.module_map = (
            dict(module_map) if module_map is not None else dict(DEFAULT_MODULE_MAP)
        )
        self.planner = planner or planning_engine.plan

    # ------------------------------------------------------------------
    # Detection handling
    def _affected_components(self, detections: Iterable[Detection]) -> set[str]:
        labels = {d.label for d in detections}
        return {self.module_map[l] for l in labels if l in self.module_map}

    def process_detections(
        self, detections: Iterable[Detection]
    ) -> Dict[str, Mapping[str, object]]:
        """Forward ``detections`` to avatar hooks and return plan entries.

        Avatar selection is delegated to
        :func:`agents.albedo.vision.consume_detections`.  Detected labels are
        translated to component names using ``module_map``.  When any relevant
        components are identified, the planning engine is executed and the
        corresponding plan entries are returned.
        """

        # Inform avatar or environment dependent modules
        avatar_vision.consume_detections(detections)

        affected = self._affected_components(detections)
        if not affected:
            return {}

        plan = self.planner()
        return {name: plan.get(name, {}) for name in affected}

    # ------------------------------------------------------------------
    def stream(
        self, frames: Iterable["np.ndarray"]
    ) -> Iterable[Dict[str, Mapping[str, object]]]:
        """Process ``frames`` and yield regeneration hints per frame."""

        for detections in self.yolo.process_stream(frames):
            yield self.process_detections(detections)


__all__ = ["VisionAdapter", "DEFAULT_MODULE_MAP"]
