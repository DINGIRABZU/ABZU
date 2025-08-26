# Chakra Overview

This table summarizes each chakra layer's role in the system along with its current semantic version, aggregated quality score, and any known warnings. Versions originate from [chakra_versions.json](chakra_versions.json), and quality scores reflect average module scores from [component_status.md](component_status.md) on a 0–4 scale.

| Chakra | Purpose | Version | Quality Score | Known Warnings |
| --- | --- | --- | --- | --- |
| Root | I/O and networking foundation | 1.0.1 | 2.0 | Network capture may require elevated permissions |
| Sacral | Emotion engine | 1.0.1 | 3.0 | Registry entries still growing |
| Solar Plexus | Learning and state transitions | 1.0.0 | 1.5 | Mutations can produce unstable states |
| Heart | Voice avatar configuration and memory storage | 1.0.1 | 3.0 | Vector store requires running database |
| Throat | Prompt orchestration and agent interface | 1.0.0 | 3.0 | None currently |
| Third Eye | Insight, QNL processing, biosignal narration | 1.0.1 | 3.0 | QNL engine emits occasional warnings |
| Crown | High-level orchestration | 1.0.1 | 2.5 | Startup scripts assume local model availability |
