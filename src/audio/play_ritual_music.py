"""Compose short ritual music based on emotion and play it.

When the optional :mod:`soundfile` dependency is available the waveform is
written and played using that library. If :mod:`soundfile` cannot be imported,
tones are synthesized directly with NumPy and played back via
``simpleaudio`` with the output also saved using the standard :mod:`wave`
module.
"""

from __future__ import annotations

import argparse
import base64
import json
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from threading import Thread

import numpy as np

try:  # pragma: no cover - optional dependency
    import soundfile as sf
except Exception:  # pragma: no cover - optional dependency
    sf = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import simpleaudio as sa
except Exception:  # pragma: no cover - optional dependency
    sa = None  # type: ignore

from core import expressive_output
from INANNA_AI import emotion_analysis, sonic_emotion_mapper
from MUSIC_FOUNDATION import layer_generators
from MUSIC_FOUNDATION.inanna_music_COMPOSER_ai import (
    SCALE_MELODIES,
    load_emotion_music_map,
    select_music_params,
)
from MUSIC_FOUNDATION.synthetic_stego_engine import encode_phrase

EMOTION_MAP = Path(__file__).resolve().parent / "emotion_music_map.yaml"
RITUAL_PROFILE = Path(__file__).resolve().parent / "ritual_profile.json"

# Small overlay samples encoded as base64 WAV data
ARCHETYPE_MIXES: dict[str, str] = {
    "albedo": (
        "UklGRtwBAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YbgBAAAAAGYAzQA0AZoBAAJmAsoC"
        "LgOSA/QDVQS2BBUFcwXPBSoGhAbbBjEHhgfYBygIdgjDCA0JVAmZCdwJHQpaCpYKzgoECzcLZwuUC78L"
        "5gsLDCwMSgxlDH0MkgykDLIMvgzGDMsMzAzLDMYMvgyyDKQMkgx9DGUMSgwsDAsM5gu/C5QLZws3CwQL"
        "zgqWCloKHQrcCZkJVAkNCcMIdggoCNgHhgcxB9sGhAYqBs8FcwUVBbYEVQT0A5IDLgPKAmYCAAKaATQB"
        "zQBmAAAAmf8y/8v+Zf7//Zn9Nf3R/G38C/yq+0n76vqM+jD61fl7+ST5zvh5+Cf41/eJ9zz38var9mb2"
        "I/bi9aX1afUx9fv0yPSY9Gv0QPQZ9PTz0/O185rzgvNt81vzTfNB8znzNPMz8zTzOfNB803zW/Nt84Lz"
        "mvO189Pz9PMZ9ED0a/SY9Mj0+/Qx9Wn1pfXi9SP2Zvar9vL2PPeJ99f3J/h5+M74JPl7+dX5MPqM+ur6"
        "Sfuq+wv8bfzR/DX9mf3//WX+y/4y/5n/AABmAM0ANAGaAQACZgLKAi4DkgP0A1UEtgQVBXMFzwUqBoQG"
        "2wYxBw=="
    ),
    "nigredo": (
        "UklGRtwBAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YbgBAAAAAJoANAHNAWYC/AKSAyUE"
        "tgREBc8FVwbbBlwH2AdQCMMIMQmZCf0JWgqyCgQLTwuUC9MLCww7DGUMiAykDLkMxgzMDMsMwgyyDJwM"
        "fQxYDCwM+Qu/C34LNwvpCpYKPArcCXcJDQmdCCgIrwcxB7AGKgahBRUFhgT0A2ADygIzApoBAQFmAMz/"
        "Mv+Y/v/9Z/3R/Dz8qvsa+4z6Avp7+fj4efj/94n3F/er9kT24vWH9TH14fSY9FX0GfTj87XzjfNt81Pz"
        "QfM28zPzNvNB81PzbfON87Xz4/MZ9FX0mPTh9DH1h/Xi9UT2q/YX94n3//d5+Pj4e/kC+oz6Gvuq+zz8"
        "0fxn/f/9mP4y/8z/ZgABAZoBMwLKAmAD9AOGBBUFoQUqBrAGMQevBygInQgNCXcJ3Ak8CpYK6Qo3C34L"
        "vwv5CywMWAx9DJwMsgzCDMsMzAzGDLkMpAyIDGUMOwwLDNMLlAtPCwQLsgpaCv0JmQkxCcMIUAjYB1wH"
        "2wZXBs8FRAW2BCUEkgP8AmYCzQE0AZoAAABl/8v+Mv6Z/QP9bfza+0n7u/ow+qj5JPmj+Cf4r/c89872"
        "ZvYC9g=="
    ),
    "rubedo": (
        "UklGRtwBAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YbgBAAAAAM0AmgFmAi4D9AO2BHMF"
        "KgbbBoYHKAjDCFQJ3AlaCs4KNwuUC+YLLAxlDJIMsgzGDMwMxgyyDJIMZQwsDOYLlAs3C84KWgrcCVQJ"
        "wwgoCIYH2wYqBnMFtgT0Ay4DZgKaAc0AAAAy/2X+mf3R/Av8SfuM+tX5JPl5+Nf3PPer9iP2pfUx9cj0"
        "a/QZ9NPzmvNt803zOfMz8znzTfNt85rz0/MZ9Gv0yPQx9aX1I/ar9jz31/d5+CT51fmM+kn7C/zR/Jn9"
        "Zf4y/wAAzQCaAWYCLgP0A7YEcwUqBtsGhgcoCMMIVAncCVoKzgo3C5QL5gssDGUMkgyyDMYMzAzGDLIM"
        "kgxlDCwM5guUCzcLzgpaCtwJVAnDCCgIhgfbBioGcwW2BPQDLgNmApoBzQAAADL/Zf6Z/dH8C/xJ+4z6"
        "1fkk+Xn41/c896v2I/al9TH1yPRr9Bn00/Oa823zTfM58zPzOfNN823zmvPT8xn0a/TI9DH1pfUj9qv2"
        "PPfX93n4JPnV+Yz6SfsL/NH8mf1l/jL/AADNAJoBZgIuA/QDtgRzBSoG2waGBygIwwhUCdwJWgrOCjcL"
        "lAvmCw=="
    ),
    "citrinitas": (
        "UklGRtwBAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YbgBAAAAAAEBAAL8AvQD5QTPBbAG"
        "hgdQCA0JuwlaCukKZwvTCywMcgykDMIMzAzCDKQMcgwsDNMLZwvpCloKuwkNCVAIhgewBs8F5QT0A/wC"
        "AAIBAQAA/v7//QP9C/wa+zD6T/l5+K/38vZE9qX1FvWY9Cz00/ON81vzPfMz8z3zW/ON89PzLPSY9Bb1"
        "pfVE9vL2r/d5+E/5MPoa+wv8A/3//f7+AAABAQAC/AL0A+UEzwWwBoYHUAgNCbsJWgrpCmcL0wssDHIM"
        "pAzCDMwMwgykDHIMLAzTC2cL6QpaCrsJDQlQCIYHsAbPBeUE9AP8AgACAQEAAP7+//0D/Qv8Gvsw+k/5"
        "efiv9/L2RPal9Rb1mPQs9NPzjfNb8z3zM/M981vzjfPT8yz0mPQW9aX1RPby9q/3efhP+TD6GvsL/AP9"
        "//3+/gAAAQEAAvwC9APlBM8FsAaGB1AIDQm7CVoK6QpnC9MLLAxyDKQMwgzMDMIMpAxyDCwM0wtnC+kK"
        "Wgq7CQ0JUAiGB7AGzwXlBPQD/AIAAgEBAAD+/v/9A/0L/Br7MPpP+Xn4r/fy9kT2pfUW9Zj0LPTT843z"
        "W/M98w=="
    ),
}


@lru_cache(maxsize=1)
def load_ritual_profile(path: Path = RITUAL_PROFILE) -> dict:
    """Return ritual mappings loaded from ``path`` if available.

    Results are cached to avoid repeated file reads.
    """
    if path.exists():
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return {k: v for k, v in data.items() if isinstance(v, dict)}
    return {}


def _get_archetype_mix(archetype: str, sample_rate: int = 44100) -> np.ndarray:
    """Return a small overlay sample for ``archetype`` or synthesize one."""

    def _synth() -> np.ndarray:
        duration = 0.5
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        freq_map = {
            "nigredo": 220.0,
            "albedo": 440.0,
            "rubedo": 660.0,
            "citrinitas": 880.0,
        }
        freq = freq_map.get(archetype.lower(), 440.0)
        tone = 0.05 * np.sin(2 * np.pi * freq * t)
        return tone.astype(np.float32)

    data = ARCHETYPE_MIXES.get(archetype.lower())
    if data:
        if sf is not None:
            raw = base64.b64decode(data)
            wave, _ = sf.read(BytesIO(raw), dtype="float32")
            return wave.astype(np.float32)
        return _synth()

    return _synth()


def _note_to_freq_simple(note: str) -> float:
    """Convert a basic note name like ``C4`` to a frequency in Hertz."""

    offsets = {
        "C": -9,
        "C#": -8,
        "Db": -8,
        "D": -7,
        "D#": -6,
        "Eb": -6,
        "E": -5,
        "F": -4,
        "F#": -3,
        "Gb": -3,
        "G": -2,
        "G#": -1,
        "Ab": -1,
        "A": 0,
        "A#": 1,
        "Bb": 1,
        "B": 2,
    }
    name = note[:-1]
    octave = int(note[-1])
    semitone = offsets.get(name, 0) + 12 * (octave - 4)
    return 440.0 * (2 ** (semitone / 12))


def _synthesize_melody(
    tempo: float,
    melody: list[str],
    *,
    wave_type: str = "sine",
    sample_rate: int = 44100,
) -> np.ndarray:
    """Generate a simple waveform for ``melody`` without ``soundfile``."""

    beat_duration = 60.0 / float(tempo)
    segments: list[np.ndarray] = []
    for note in melody:
        freq = _note_to_freq_simple(str(note))
        t = np.linspace(
            0, beat_duration, int(sample_rate * beat_duration), endpoint=False
        )
        if wave_type == "square":
            seg = 0.5 * np.sign(np.sin(2 * np.pi * freq * t))
        else:
            seg = 0.5 * np.sin(2 * np.pi * freq * t)
        segments.append(seg.astype(np.float32))
    wave = np.concatenate(segments) if segments else np.zeros(1, dtype=np.float32)
    max_val = float(np.max(np.abs(wave)))
    if max_val > 0:
        wave /= max_val
    return wave.astype(np.float32)


def _write_wav(path: Path, data: np.ndarray, sample_rate: int = 44100) -> None:
    """Write ``data`` to ``path`` as a mono WAV using the standard library."""

    path.parent.mkdir(parents=True, exist_ok=True)
    import wave

    clipped = np.clip(data, -1.0, 1.0)
    pcm = (clipped * 32767).astype("<i2")
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())


def compose_ritual_music(
    emotion: str,
    ritual: str,
    *,
    archetype: str | None = None,
    hide: bool = False,
    out_path: Path = Path("ritual.wav"),
    sample_rate: int = 44100,
    output_dir: Path = Path("."),
) -> Path:
    """Generate a simple melody and optionally hide ritual steps.

    The WAV file is written to ``output_dir / out_path`` and played back. The
    ``sample_rate`` parameter controls the synthesis rate and defaults to
    ``44100``. Uses ``soundfile`` when available; otherwise the melody is
    synthesized with NumPy, written using the :mod:`wave` module and played
    through ``simpleaudio`` if installed.
    """
    if archetype is None:
        try:
            archetype = emotion_analysis.get_current_archetype()
        except Exception:
            archetype = "Everyman"

    if not out_path.is_absolute():
        out_path = output_dir / out_path

    mapping = load_emotion_music_map(EMOTION_MAP)
    params = sonic_emotion_mapper.map_emotion_to_sound(emotion, archetype)

    tempo, _scale, melody, rhythm = select_music_params(
        emotion, mapping, params["tempo"]
    )

    if params.get("scale"):
        melody = SCALE_MELODIES.get(params["scale"], melody)

    wave_type = (
        "square"
        if any("guitar" in t or "trumpet" in t for t in params.get("timbre", []))
        else "sine"
    )

    if sf is not None:
        wave = layer_generators.compose_human_layer(
            tempo,
            melody,
            sample_rate=sample_rate,
            wav_path=str(out_path),
            wave_type=wave_type,
        )
    else:
        wave = _synthesize_melody(
            tempo,
            melody,
            wave_type=wave_type,
            sample_rate=sample_rate,
        )

    mix = _get_archetype_mix(archetype, sample_rate)
    if mix.size:
        if mix.size < wave.size:
            mix = np.pad(mix, (0, wave.size - mix.size))
        wave = wave + mix[: wave.size]
        max_val = float(np.max(np.abs(wave)))
        if max_val > 0:
            wave /= max_val

    if sf is not None:
        sf.write(out_path, wave, sample_rate)
    else:
        _write_wav(out_path, wave, sample_rate)

    if hide:
        profile = load_ritual_profile()
        phrase = " ".join(profile.get(ritual, {}).get(emotion, []))
        if phrase:
            stego_wave = encode_phrase(phrase)
            if stego_wave.size < wave.size:
                stego_wave = np.pad(stego_wave, (0, wave.size - stego_wave.size))
            wave = wave[: stego_wave.size] + stego_wave[: wave.size]
            max_val = float(np.max(np.abs(wave)))
            if max_val > 0:
                wave /= max_val
            if sf is not None:
                sf.write(out_path, wave, sample_rate)
            else:
                _write_wav(out_path, wave, sample_rate)

    if sf is not None:
        Thread(
            target=expressive_output.play_audio, args=(out_path,), daemon=True
        ).start()
    elif sa is not None:
        pcm = (np.clip(wave, -1.0, 1.0) * 32767).astype(np.int16)
        Thread(
            target=lambda: sa.play_buffer(pcm, 1, 2, sample_rate).wait_done(),
            daemon=True,
        ).start()
    return out_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Play ritual music")
    parser.add_argument("--emotion", default="neutral", help="Emotion driving the tone")
    parser.add_argument("--ritual", default="\u2609", help="Ritual symbol")
    parser.add_argument(
        "--stego",
        action="store_true",
        help="Hide ritual phrase inside the WAV",
    )
    parser.add_argument("--output", default="ritual.wav", help="Output WAV path")
    args = parser.parse_args(argv)

    compose_ritual_music(
        args.emotion, args.ritual, hide=args.stego, out_path=Path(args.output)
    )
    # Playback handled inside compose_ritual_music


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
