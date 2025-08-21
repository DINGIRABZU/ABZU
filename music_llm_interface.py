from __future__ import annotations

"""Interface between the music analysis pipeline and LLM CROWN.

This module exposes a small utility that analyses an audio or MIDI file and
feeds the resulting features to the :class:`rag.orchestrator.MoGEOrchestrator`.
Results from the music pipeline and the language model are combined into a
single JSON structure printed to ``stdout``.  The entry point can be invoked
from the command line via ``python music_llm_interface.py <audio_or_midi>``.
"""

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any, Dict

import numpy as np

try:  # pragma: no cover - optional dependency for MIDI support
    import pretty_midi
except Exception:  # pragma: no cover - optional dependency
    pretty_midi = None  # type: ignore

try:  # pragma: no cover - optional dependency for WAV writing
    import soundfile as sf
except Exception:  # pragma: no cover - optional dependency
    sf = None  # type: ignore

from INANNA_AI.emotion_analysis import analyze_audio_emotion
from pipeline.music_analysis import (MusicAnalysisResult, analyze_music,
                                     extract_high_level_features)
from rag.orchestrator import MoGEOrchestrator


def _analyze_midi(path: Path) -> MusicAnalysisResult:
    """Return :class:`MusicAnalysisResult` for ``path`` MIDI file.

    The function synthesises the MIDI file to a temporary audio waveform and
    then extracts the same high level features as :func:`analyze_music`.
    """

    if pretty_midi is None:
        raise RuntimeError("pretty_midi library not installed")

    midi = pretty_midi.PrettyMIDI(str(path))
    sr = 44100
    samples = (
        midi.fluidsynth(fs=sr)
        if hasattr(midi, "fluidsynth")
        else midi.synthesize(fs=sr)
    )

    features = extract_high_level_features(samples, sr)

    # ``analyze_audio_emotion`` expects a file path, so write the waveform to a
    # temporary WAV file.
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        if sf is not None:
            sf.write(tmp_path, samples, sr)
        else:  # pragma: no cover - ``wave`` fallback when soundfile missing
            import wave

            data = np.clip(samples, -1.0, 1.0)
            data = (data * 32767).astype(np.int16)
            with wave.open(str(tmp_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                wf.writeframes(data.tobytes())
    try:
        emotion = analyze_audio_emotion(str(tmp_path))
    finally:
        tmp_path.unlink(missing_ok=True)

    metadata = {"path": str(path), "sr": sr, "duration": len(samples) / sr}
    return MusicAnalysisResult(features=features, emotion=emotion, metadata=metadata)


def analyze_path(path: Path) -> MusicAnalysisResult:
    """Dispatch to the appropriate analysis routine for ``path``."""

    if path.suffix.lower() in {".mid", ".midi"}:
        return _analyze_midi(path)
    return analyze_music(path)


def run_interface(
    path: Path, orchestrator: MoGEOrchestrator | None = None
) -> Dict[str, Any]:
    """Analyse ``path`` and query the LLM through ``orchestrator``."""

    analysis = analyze_path(path)
    payload = analysis.__dict__

    orch = orchestrator or MoGEOrchestrator()
    prompt = f"LLM CROWN, consider the following music analysis:\n{json.dumps(payload)}"
    llm_reply = orch.handle_input(prompt)
    return {"analysis": payload, "llm_response": llm_reply}


def main(argv: list[str] | None = None) -> None:
    """Command line interface for the music LLM bridge."""

    parser = argparse.ArgumentParser(description="Analyse music and query LLM CROWN")
    parser.add_argument("file", type=Path, help="Path to an audio or MIDI file")
    args = parser.parse_args(argv)

    result = run_interface(args.file)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
