# Stage B Rehearsal Refresh — 2025-09-21

## Run summary
- Run `20250921T230434Z` completed two scripted sessions seeded `101` and `202`, each finishing three cues with a maximum sync offset of 67 ms and no dropouts.【F:logs/stage_b/20250921T230434Z/rehearsals/summary.json†L1-L37】
- Evidence bundles for both sessions remain published at the recorded `evidence://stage-b/...` URIs with retained telemetry indexes for quick inspection.【F:logs/stage_b/20250921T230434Z/rehearsals/rehearsal_manifest.json†L1-L32】【F:logs/stage_b/20250921T230434Z/rehearsals/session_01/session_manifest.json†L1-L23】

## Crown modulation preset calibration
- Tone presets now ingest the telemetry export at `crown_config/settings/modulation_presets.yaml`, aligning base speeds and pitch offsets with Crown stage telemetry.
- The arrival cue maps to the **albedo** tone and retains a neutral 1.00× speed after matching the 1.0 s audio/video durations captured during the scripted demo.【F:crown_config/settings/modulation_presets.yaml†L1-L15】【F:logs/stage_c/20250923T221242Z-stage_c2_demo_storyline/demo_storyline/telemetry/events.jsonl†L1-L1】
- The mission handoff cue drives the **rubedo** tone, adopting a 0.952× speed and reduced 0.433 pitch boost to correct the 67 ms lag observed between 1.4 s audio and 1.333 s video stems.【F:crown_config/settings/modulation_presets.yaml†L16-L26】【F:logs/stage_c/20250923T221242Z-stage_c2_demo_storyline/demo_storyline/telemetry/events.jsonl†L2-L2】
- The closing harmonic swell calibrates the **lunar** tone at 0.989× speed with a −0.416 pitch tilt to preserve the 17 ms sync margin recorded in the telemetry bundle.【F:crown_config/settings/modulation_presets.yaml†L27-L37】【F:logs/stage_c/20250923T221242Z-stage_c2_demo_storyline/demo_storyline/telemetry/events.jsonl†L3-L3】
- The **nigredo** tone now mirrors the Stage B rehearsal resonance envelope by deriving its 0.933× speed from the measured 0.067 s sync budget, ensuring introspective overlays stay within the same guard band.【F:crown_config/settings/modulation_presets.yaml†L37-L44】【F:logs/stage_b/20250921T230434Z/rehearsals/summary.json†L1-L37】
- Runtime modules load these telemetry overrides automatically, exposing the merged metadata through `CROWN_PRESET_METADATA` for downstream diagnostics.【F:INANNA_AI/voice_layer_albedo.py†L1-L85】【F:INANNA_AI/voice_layer_albedo.py†L89-L112】

## Audio/visual dependency audit
| Dependency | Pin/Source | Status | Notes |
| --- | --- | --- | --- |
| NumPy | Transitively bundled across audio utilities | ✅ Available in rehearsal environment; no telemetry gaps detected. |
| PyDub & FFmpeg | `pydub==0.25.1` via `scripts/setup_audio_env.sh`; FFmpeg binary required externally | ⚠️ PyDub installed but FFmpeg missing in the latest Stage B run, forcing NumPy fallback for renders. Remedy via package manager before next session.【F:scripts/setup_audio_env.sh†L33-L58】【F:logs/stage_b/20250921T230434Z/rehearsals/fallbacks.json†L1-L20】 |
| Librosa | `librosa==0.11.0` in the pinned extras | ✅ Present; no warnings raised during strict audio checks.【F:scripts/setup_audio_env.sh†L33-L58】 |
| OpenSMILE | `opensmile==2.6.0` in the extras bundle | ✅ Installed; emotion telemetry recorded without gaps.【F:scripts/setup_audio_env.sh†L33-L58】 |
| EmotiVoice | `EmotiVoice==0.2.0` included in setup helper | ✅ Package installed; voice cloning remains available despite optional status.【F:scripts/setup_audio_env.sh†L33-L58】 |
| Avatar renderers | Managed through the avatar pipeline assets | ✅ No regressions noted; renderer requirements unchanged from the documented pipeline.【F:docs/avatar_pipeline.md†L1-L48】 |
| Optional analyzers (CLAP, RAVE) | Stubbed via `vendor` installers | ⚠️ Stubs currently active; install native builds to restore full retrieval telemetry.【F:scripts/setup_audio_env.sh†L60-L74】【F:logs/stage_b/20250921T230434Z/rehearsals/fallbacks.json†L1-L20】 |

## Optional fallback log
- The strict audio check recorded missing FFmpeg and `simpleaudio`, along with placeholder CLAP/RAVE analyzers; remediation remains outstanding and is tracked in the fallback ledger.【F:logs/stage_b/20250921T230434Z/rehearsals/fallbacks.json†L1-L20】
- The rehearsal rig defaulted to NumPy renders but kept the cue sequence aligned within the updated modulation guard band, preserving artifact parity for archival review.【F:logs/stage_b/20250921T230434Z/rehearsals/summary.json†L1-L37】【F:crown_config/settings/modulation_presets.yaml†L1-L44】

