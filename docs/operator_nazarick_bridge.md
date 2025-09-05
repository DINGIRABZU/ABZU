# Operator-Nazarick Bridge

**Version:** v1.0.0
**Last updated:** 2025-09-05

This overview explains how operators converse with Nazarick servants and how those
conversations flow into data and narrative layers.

## Vanna Data Agent Workflow
- Operators ask questions in natural language.
- The `vanna_data` agent converts the prompt into SQL and executes the query.
- Raw rows are persisted in mental memory while a narrative summary is appended to
  `data/narrative.log` for later storytelling.

## Nazarick Channels & Personas
- Servant agents occupy chakra-aligned channels such as the Orchestration Master,
  Prompt Orchestrator, QNL Engine, and Memory Scribe.
- Each agent maintains a defined personality that colors its responses and
  responsibilities.
- Channel hierarchy ensures messages travel through the proper layers before
  reaching the operator.

## Operator Web Console
- The Nazarick Web Console lists active agents and opens dedicated chat rooms.
- Operators can issue commands, review responses, and stream media from each
  servant.
- Narrative logs written by Bana and Vanna are available in the console for
  review alongside real-time dialogue.

