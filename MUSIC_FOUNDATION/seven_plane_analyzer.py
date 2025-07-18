import numpy as np
import librosa

try:
    import essentia.standard as ess
except Exception:  # noqa: S110
    ess = None

from .inanna_music_COMPOSER_ai import chroma_to_qnl


def analyze_seven_planes(waveform: np.ndarray, sample_rate: int) -> dict:
    """Compute musical features mapped to seven metaphysical planes."""
    planes = {}

    # Physical plane: amplitude and spectral energy
    rms = librosa.feature.rms(y=waveform).mean()
    spectrum = np.abs(librosa.stft(waveform))
    planes["physical"] = {
        "rms": float(rms),
        "spectrum_mean": float(spectrum.mean()),
    }

    # Emotional plane: chromagram and RMS energy
    chroma = librosa.feature.chroma_stft(y=waveform, sr=sample_rate)
    planes["emotional"] = {
        "chromagram": np.mean(chroma, axis=1).tolist(),
        "rms_energy": float(rms),
    }

    # Mental plane: tempo, beats, and onsets
    tempo, beats = librosa.beat.beat_track(y=waveform, sr=sample_rate)
    onsets = librosa.onset.onset_detect(y=waveform, sr=sample_rate)
    planes["mental"] = {
        "tempo": float(tempo),
        "beats": int(len(beats)),
        "onsets": int(len(onsets)),
    }

    # Astral plane: spectral centroid and rolloff
    centroid = librosa.feature.spectral_centroid(y=waveform, sr=sample_rate).mean()
    rolloff = librosa.feature.spectral_rolloff(y=waveform, sr=sample_rate).mean()
    planes["astral"] = {
        "centroid": float(centroid),
        "rolloff": float(rolloff),
    }

    # Etheric plane: MFCCs and harmonic-to-noise ratio
    mfcc = librosa.feature.mfcc(y=waveform, sr=sample_rate, n_mfcc=13)
    etheric = {"mfcc": np.mean(mfcc, axis=1).tolist()}
    if ess is not None:
        hnr = ess.Harmonicity()(waveform.astype(float))[1]
        etheric["hnr"] = float(hnr)
    else:
        etheric["hnr"] = None
    planes["etheric"] = etheric

    # Celestial plane: high-frequency content and rough reverb estimate
    freqs = librosa.fft_frequencies(sr=sample_rate)
    high_band = spectrum[freqs > 8000]
    hf_energy = float(high_band.mean()) if high_band.size else 0.0
    energy = spectrum.sum(axis=0)
    reverb_est = float(energy[-5:].mean() / energy.max()) if energy.size else 0.0
    planes["celestial"] = {
        "high_freq_energy": hf_energy,
        "reverb_estimate": reverb_est,
    }

    # Divine plane: QNL glyphs or fractal signatures
    avg_chroma = np.mean(chroma, axis=1)
    qnl_phrases = [p["qnl_phrase"] for p in chroma_to_qnl(avg_chroma)]
    planes["divine"] = {
        "qnl_phrases": qnl_phrases,
        "signature": f"fractal-{len(waveform)}",
    }

    return planes
