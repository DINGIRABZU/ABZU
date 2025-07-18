from __future__ import annotations

"""Simple dialogue manager blending audio and text context."""

from typing import Dict

from . import corpus_memory


# Reply templates for each core.  ``emotion`` and ``classification`` are inserted
# to blend audio cues with the textual input.
CORE_TEMPLATES = {
    "surface": "[Surface] {snippet} ({emotion}/{classification}) You said: '{text}'",
    "deep": "[Deep] {snippet} ({emotion}/{classification}) Your words carry depth: '{text}'",
    "umbra": "[Umbra] {snippet} ({emotion}/{classification}) Shadows echo: '{text}'",
    "albedo": "[Albedo] {snippet} ({emotion}/{classification}) Reflecting: '{text}'",
}


class ResponseManager:
    """Select replies based on emotional and environmental cues.

    The manager receives the emotional ``state`` and ``classification`` detected
    by :class:`listening_engine.ListeningEngine` and chooses one of the
    Surface/Deep/Umbra/Albedo cores. A search against the CORPUS MEMORY is
    performed using :func:`corpus_memory.search_corpus` with a query that blends
    the transcript, emotion and classification.  The chosen template then
    incorporates the snippet and audio context into the final text reply.
    """

    def choose_core(self, emotion: str, classification: str) -> str:
        """Return core name for the given emotion and environment."""
        emotion = emotion.lower()
        classification = classification.lower()
        if classification == "noise":
            return "umbra"
        if emotion == "excited":
            return "surface"
        if emotion == "calm":
            return "albedo"
        return "deep"

    def generate_reply(self, text: str, info: Dict[str, str]) -> str:
        """Generate a text reply blending audio and textual context.

        Parameters
        ----------
        text:
            The transcript recognized from speech.
        info:
            Output of :class:`listening_engine.ListeningEngine` containing at
            least ``emotion`` and ``classification`` keys.

        Returns
        -------
        str
            The rendered reply text including a snippet from CORPUS MEMORY.
        """
        emotion = info.get("emotion", "neutral")
        classification = info.get("classification", "")
        query = f"{text} {emotion} {classification}".strip()
        snippets = corpus_memory.search_corpus(query, top_k=1)
        snippet = snippets[0][1] if snippets else ""
        core = self.choose_core(emotion, classification)
        template = CORE_TEMPLATES.get(core, CORE_TEMPLATES["surface"])
        return template.format(
            snippet=snippet,
            text=text,
            emotion=emotion,
            classification=classification,
        )


__all__ = ["ResponseManager", "CORE_TEMPLATES"]
