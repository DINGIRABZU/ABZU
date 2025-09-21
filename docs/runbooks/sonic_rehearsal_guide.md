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

The command verifies that the core `audio` extras stack is ready.
See [Audio Stack Dependencies](../audio_stack.md) for the full
degradation matrix covering optional packages such as CLAP or RAVE.

## Provisioning steps

1. Install the Python packages inside the rehearsal virtual environment using
   the pinned versions:

   ```bash
   pip install \
       pydub==0.25.1 \
       simpleaudio==1.0.4 \
       soundfile==0.13.1 \
       librosa==0.11.0 \
       opensmile==2.6.0 \
       EmotiVoice==0.2.0
   ```

   Optional integrations (CLAP, RAVE, Demucs, Spleeter, EmotiVoice) can be
   added afterwards depending on the rehearsal focus.

2. Provision FFmpeg with the system package manager (example for Ubuntu):

   ```bash
   sudo apt-get update
   sudo apt-get install -y ffmpeg
   ```

   Install `libasound2-dev` on Debian/Ubuntu hosts before compiling
   `simpleaudio` so the ALSA headers are available.

3. Confirm the toolchain:

   ```bash
   python -m audio.check_env --strict
   ```

   The command must report that FFmpeg, pydub and simpleaudio are present. It
   will log warnings for missing optional analyzers (e.g. CLAP) so operators
   can record temporary degradations in the rehearsal log.

4. Run the Stage B rehearsal setup script to confirm Ardour/Carla tooling:

   ```bash
   bash scripts/setup_audio_env.sh
   ```

   The script installs the pinned audio dependencies, runs the strict audio
   validation helper, and executes the
   `modulation_arrangement.check_daw_availability` preflight. When Ardour or
   Carla binaries are missing, it logs a warning and Stage B exports fall back
   to audio renders without generating the corresponding session files.【F:scripts/setup_audio_env.sh†L1-L42】

5. Export the backend for local shells when invoking rehearsal utilities:

   ```bash
   export AUDIO_BACKEND=pydub
   ```

6. Attach the validation transcript to the Stage B rehearsal checklist so the
   audio lab can track regressions across runs.
