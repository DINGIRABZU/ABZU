"""
music_foundation.py
INANNA_AI — QNL Sonic Decoder

This module loads an MP3 file, converts it to waveform, analyzes rhythm, pitch, and harmonic structure,
and prepares it for QNL transformation (to be defined in qnl_engine or human_music_to_qnl_converter).

Requirements:
    pip install librosa soundfile numpy scipy
"""

import librosa
import numpy as np
import soundfile as sf
import os

class MusicInterpreter:
    def __init__(self, file_path):
        self.file_path = file_path
        self.waveform = None
        self.sample_rate = None
        self.tempo = None
        self.beats = None
        self.chromagram = None

    def load_audio(self):
        self.waveform, self.sample_rate = librosa.load(self.file_path, sr=None, mono=True)
        print(f"✅ Audio loaded: {self.file_path}")
        print(f"📐 Sample Rate: {self.sample_rate}, Duration: {len(self.waveform) / self.sample_rate:.2f} sec")

    def analyze_rhythm(self):
        self.tempo, self.beats = librosa.beat.beat_track(y=self.waveform, sr=self.sample_rate)
        print(f"🕒 Estimated Tempo: {self.tempo:.2f} BPM")
        return self.tempo, self.beats

    def analyze_harmony(self):
        chroma = librosa.feature.chroma_stft(y=self.waveform, sr=self.sample_rate)
        self.chromagram = chroma
        avg_chroma = np.mean(chroma, axis=1)
        print("🎶 Average Chroma Values (Pitch Classes):")
        for i, val in enumerate(avg_chroma):
            print(f"  {librosa.midi_to_note(60 + i)}: {val:.3f}")
        return avg_chroma

    def export_preview(self, output_path="music_preview.wav"):
        """Save waveform as a standard WAV file for playback.

        The directory for ``output_path`` is created if it does not exist.
        """
        directory = os.path.dirname(output_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        sf.write(output_path, self.waveform, self.sample_rate)
        print(f"💾 Exported WAV preview to: {output_path}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="INANNA_AI — Music Analysis Core")
    parser.add_argument("mp3_file", help="Path to the MP3 file to analyze")
    args = parser.parse_args()

    interpreter = MusicInterpreter(args.mp3_file)
    interpreter.load_audio()
    interpreter.analyze_rhythm()
    interpreter.analyze_harmony()
    interpreter.export_preview()
