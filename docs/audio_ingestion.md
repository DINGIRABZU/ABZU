# Audio Ingestion

This guide outlines how Spiral OS loads audio files and enriches them with optional features such as tempo and key detection.

## Loading with `librosa`

`librosa` reads most common audio formats into NumPy arrays:

```python
import librosa
samples, sr = librosa.load("song.wav", sr=44100, mono=True)
```

Specify the target sample rate with `sr` and set `mono=False` to keep stereo channels. The returned `samples` array is then passed to the processing pipeline.

## Optional Essentia Features

When the [Essentia](https://essentia.upf.edu) package is installed, Spiral OS can detect musical characteristics. The following snippet extracts the key and tempo:

```python
import essentia.standard as es
key, scale, strength = es.KeyExtractor()(samples)
tempo, confidence = es.RhythmExtractor2013(method="multifeature")(samples)
```

Install Essentia with `pip install essentia` or build from source following the [official instructions](https://github.com/MTG/essentia#installation). Without Essentia the system falls back to `librosa.beat.tempo` for tempo estimation.

## Integrating CLAP Embeddings

If a CLAP (Contrastive Language–Audio Pretraining) model is available, you can embed each clip for retrieval and analysis:

```python
from transformers import ClapProcessor, ClapModel

processor = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
model = ClapModel.from_pretrained("laion/clap-htsat-unfused")

inputs = processor(audios=samples, return_tensors="pt")
embeddings = model.get_audio_features(**inputs).squeeze()
```

Store these vectors alongside other metadata to enable similarity search through the vector memory.

## Vocal Isolation

When one of [Demucs](https://github.com/facebookresearch/demucs),
[Spleeter](https://github.com/deezer/spleeter) or
[Open-Unmix](https://github.com/sigsep/open-unmix-pytorch) is available you can
split a track into separate stems. Spiral OS provides a small helper for this in
:mod:`vocal_isolation`:

```python
from pathlib import Path
from vocal_isolation import separate_stems

stems = separate_stems(Path("song.wav"))  # uses Demucs by default
vocals = stems["vocals"]

# Keep the generated files
separate_stems(Path("song.wav"), output_dir=Path("stems"))
```

Specify ``method="spleeter"`` to invoke ``spleeter separate -p spleeter:5stems``
instead or ``method="umx"`` to use the Open-Unmix backend:

```python
stems = separate_stems(Path("song.wav"), method="spleeter")
```

```python
stems = separate_stems(Path("song.wav"), method="umx")
```

The returned dictionary maps stem names such as ``vocals`` or ``drums`` to the
paths of the generated files.

## Arranging Stems

Use :mod:`modulation_arrangement` to pan and mix the isolated tracks:

```python
from pathlib import Path
from modulation_arrangement import layer_stems, export_mix, export_session
from vocal_isolation import separate_stems

stems = separate_stems(Path("song.wav"))
mix = layer_stems(stems, pans=[-1, 1], volumes=[-3, -6])
export_mix(mix, Path("mix.wav"))
export_session(mix, Path("mix.wav"), session_format="ardour")
```

Helper functions such as :func:`slice_loop` and :func:`apply_fades` allow quick
loop extraction and smoothing of transitions.

## Ingesting Music Books

Use `scripts/ingest_music_books.py` to embed text-based music resources such as
PDF or EPUB files. The script extracts the text with `pdfplumber` and
`unstructured` then stores short chunks in the vector memory with associated
metadata.

```bash
python scripts/ingest_music_books.py book.pdf --genre jazz --year 1975 \
    --culture US --instruments "saxophone,piano"
```

Each entry receives the ``SOURCE_TYPE`` and ``SOURCE_PATH`` of the original
file in addition to any labels you provide.
