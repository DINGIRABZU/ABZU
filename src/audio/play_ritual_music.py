"""Compose short ritual music based on emotion and play it."""

from __future__ import annotations

import argparse
import base64
from functools import lru_cache
from io import BytesIO
from pathlib import Path

import logging
import numpy as np

logger = logging.getLogger(__name__)

from . import backends

import importlib

emotion_params = importlib.import_module(".emotion_params", __package__)
stego = importlib.import_module(".stego", __package__)
waveform = importlib.import_module(".waveform", __package__)

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
        "2wYxBw==",
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
        "ZvYC9g==",
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
        "lAvmCw==",
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
        "W/M98w==",
    ),
}


@lru_cache(maxsize=None)
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
    sf_lib = backends.sf
    if data and sf_lib is not None:
        raw = base64.b64decode(data)
        wave, _ = sf_lib.read(BytesIO(raw), dtype="float32")
        return wave.astype(np.float32)

    if data:
        logger.info("soundfile not available; synthesizing tone for '%s'", archetype)
    return _synth()


def compose_ritual_music(
    emotion: str,
    ritual: str,
    *,
    archetype: str | None = None,
    hide: bool = False,
    output_dir: Path | None = None,
    sample_rate: int = 44100,
) -> Path:
    """Generate a simple melody and optionally hide ritual steps."""

    tempo, melody, wave_type, arch = emotion_params.resolve(emotion, archetype)
    logger.info("Selected archetype '%s'", arch)
    wave = waveform.synthesize(melody, tempo, wave_type)

    mix = _get_archetype_mix(arch)
    if mix.size:
        if mix.size < wave.size:
            mix = np.pad(mix, (0, wave.size - mix.size))
        wave = wave + mix[: wave.size]
        max_val = float(np.max(np.abs(wave)))
        if max_val > 0:
            wave /= max_val

    if hide:
        wave = stego.embed_phrase(wave, ritual, emotion)

    out_dir = output_dir or Path(".")
    out_path = out_dir / "ritual.wav"

    backend = backends.get_backend()
    logger.info("Using audio backend %s", backend.__class__.__name__)
    backend.play(out_path, wave, sample_rate)

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
        args.emotion,
        args.ritual,
        hide=args.stego,
        output_dir=Path(args.output).parent,
    )
    # Playback handled inside compose_ritual_music


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
