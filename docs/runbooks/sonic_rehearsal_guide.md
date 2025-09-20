# Sonic Rehearsal Guide

The sonic rehearsal ritual validates the playback pipeline before Stage B
sessions. The environment must honour the enforced `AUDIO_BACKEND=pydub`
configuration so the full pydub feature set is available during rehearsals.

## Audio backend enforcement

1. `start_spiral_os.py` now aborts when the core audio stack is incomplete.
   The script calls `python -m audio.check_env --strict` internally, so
   failures surface before any rehearsal state is mutated.
2. The backend resolver prefers `AUDIO_BACKEND=pydub` when FFmpeg is
   discoverable on `PATH`. If `ffmpeg` is missing the loader logs a hard error
   and temporarily drops to the NumPy fallback until the toolchain is fixed.
3. Operators overriding the backend to `numpy` must capture the deviation in
   the rehearsal log and schedule remediation before the next Stage B session.

## Dependency checklist

Run the validation helper before each Stage B dry run:

```bash
python -m audio.check_env --strict
```

The command verifies the following components:

- `ffmpeg` – binary required for encoding/decoding during overlays.
- `pydub` – preferred audio backend powering Stage B rehearsals.
- `simpleaudio` – realtime playback shim used by the sonic console.
- Support libraries (`librosa`, `soundfile`, `opensmile`, `clap`, `rave`).

## Provisioning steps

1. Install the Python packages inside the rehearsal virtual environment:

   ```bash
   pip install pydub simpleaudio librosa soundfile opensmile clap rave
   ```

2. Provision FFmpeg with the system package manager (example for Ubuntu):

   ```bash
   sudo apt-get update
   sudo apt-get install -y ffmpeg
   ```

3. Confirm the toolchain:

   ```bash
   python -m audio.check_env --strict
   ```

   The command must report that ffmpeg, pydub and simpleaudio are present.

4. Export the backend for local shells when invoking rehearsal utilities:

   ```bash
   export AUDIO_BACKEND=pydub
   ```

5. Attach the validation transcript to the Stage B rehearsal checklist so the
   audio lab can track regressions across runs.
