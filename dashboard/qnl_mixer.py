import io

import numpy as np

try:  # pragma: no cover - optional dependency
    import librosa
    import librosa.display
except Exception:  # pragma: no cover - optional dependency
    librosa = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import soundfile as sf
except Exception:  # pragma: no cover - optional dependency
    sf = None  # type: ignore

import matplotlib.pyplot as plt
import streamlit as st

from audio.mix_tracks import apply_audio_params, embedding_to_params
from MUSIC_FOUNDATION.qnl_utils import quantum_embed

st.set_page_config(page_title="QNL Mixer")

st.title("Real-time QNL Mixer")

uploaded = st.file_uploader("Upload WAV", type=["wav"])
text = st.text_input("QNL text", "")

if uploaded is not None:
    if librosa is None or sf is None:
        st.error("librosa and soundfile libraries are required")
    else:
        data, sr = librosa.load(uploaded, sr=44100, mono=True)
    if text:
        emb = quantum_embed(text)
        pitch, tempo, cutoff = embedding_to_params(emb)
        data = apply_audio_params(data, sr, pitch, tempo, cutoff)
    spec = np.abs(librosa.stft(data))
    db = librosa.amplitude_to_db(spec, ref=np.max)
    fig, ax = plt.subplots()
    img = librosa.display.specshow(db, sr=sr, x_axis="time", y_axis="log", ax=ax)
    ax.set(title="Spectrogram")
    fig.colorbar(img, ax=ax, format="%+2.f dB")
    st.pyplot(fig)
    buf = io.BytesIO()
    sf.write(buf, data, sr, format="WAV")
    st.audio(buf.getvalue(), format="audio/wav")
