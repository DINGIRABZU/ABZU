# Mix Tracks

`audio/mix_tracks.py` combines multiple audio stems into a single track. The
module accepts a JSON instruction file so that higher level tools or LLMs can
specify how each stem should be processed before mixing.

## Instruction Format

```json
{
  "stems": [
    {
      "file": "stems/drums.wav",
      "pitch": -2.0,
      "time": 1.1,
      "compress": {"threshold": -18.0, "ratio": 2.5}
    },
    {
      "file": "stems/bass.wav",
      "time": 0.9
    }
  ],
  "output": "mix.wav",
  "preview": {"file": "mix_preview.wav", "duration": 5.0}
}
```

Keys:

- `stems` – list of stem descriptions. Each stem may define `pitch` in
  semitones, `time` stretch factor and optional `compress` settings.
- `output` – name of the final WAV written to the `output/` directory.
- `preview` – optional preview file and duration in seconds.

## Workflow

1. Prepare the instruction JSON and source audio files.
2. Run the mixer:

   ```bash
   python -m audio.mix_tracks --instructions instructions.json
   ```

3. The script renders the full mix and a short preview to the `output/`
   directory.
