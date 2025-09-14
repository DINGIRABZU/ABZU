# Narrative Framework

This framework links raw biosignals to high‑level orchestration across the
stack.

1. **Biosignal intake** – sensors stream anonymized vitals which are shaped
   into narrative events via ingestion scripts and the narrative API
   gateway.【F:docs/nazarick_narrative_system.md†L30-L35】
2. **Bana narrative engine** – INANNA biosignals traverse the bridge into the
   bio‑adaptive narrator, persisting results to memory and log stores for later
   recall.【F:docs/bana_engine.md†L11-L17】
3. **Inanna persona** – the bridge forwards Bana events into the Albedo persona
   for stylistic rendering and reflection before passing them downstream.
4. **Razor orchestration** – structured narrative packets drive the wider
   experience pipeline, where an orchestrator routes descriptions and game
   directives into runtime systems for operator interaction.【F:NEOABZU/docs/Bana Narrator vision.md†L16-L37】

This flow provides a reproducible path from physiological signals to the
stories and scenes operators observe.
