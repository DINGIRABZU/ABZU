# Corpus Memory

This repository preserves several collections of source texts used by the music and language tools. Each directory serves a distinct purpose.

## INANNA_AI

`INANNA_AI` holds the "growth" chronicles, code fragments and guiding letters for the INANNA project. Files are primarily Markdown with descriptive titles followed by a unique hash, for example `INANNA GROWTH #2 20645dfc251d80fdac0cc1db79e5e516.md`. Additional helper files like `secrets.env.example` and summary CSVs may also appear.

## GENESIS

`GENESIS` contains foundational doctrines and laws written in Markdown. The files end in an underscore such as `GENESIS_.md` or `LAWS_RECURSION_.md`. They capture the earliest principles of the project.

## IGNITION

`IGNITION` starts the narrative with seeding texts like `EA_ENUMA_ELISH_.md`. These Markdown files provide mythic or historical context that "ignites" the rest of the corpus.

## QNL_LANGUAGE

`QNL_LANGUAGE` stores drafts and versions of the Quantum Narrative Language. File names combine a short title with a trailing hash, e.g. `3RD VERSION 20445dfc251d804b9a50c21461a203f0.md`. These Markdown documents may embed code blocks illustrating the syntax.

## File Format and Naming

All corpus entries use the `.md` extension and may contain rich Markdown including headings, lists and code snippets. Titles often contain spaces. A suffix of hexadecimal digits uniquely identifies each file. Underscores at the end of a name indicate canonical texts.

## Adding New Texts

To add a new memory fragment, create a Markdown file in the appropriate directory. Follow the existing naming convention: a descriptive title followed by a space and an ID or underscore, ending with `.md`. Keep commit messages short and meaningful so other collaborators can track additions easily.

## Vector memory

`vector_memory.py` stores short text entries inside a Chroma database. The
directory defaults to `data/vector_memory` but can be changed by setting the
`VECTOR_DB_PATH` environment variable. Each entry is embedded with
`qnl_utils.quantum_embed` and timestamped so older items gradually decay in
relevance.  Use :func:`vector_memory.add_vector` and
:func:`vector_memory.search` programmatically to store and retrieve snippets.

## Corpus memory commands

The module `INANNA_AI.corpus_memory` exposes a small command line utility:

```bash
python -m INANNA_AI.corpus_memory --add "hello world" --tone joy
python -m INANNA_AI.corpus_memory --search "hello" --top 5
python -m INANNA_AI.corpus_memory --reindex
```

`--add` embeds a string and stores it with optional tone metadata. `--search`
retrieves the best matching snippets, and `--reindex` rebuilds the persistent
index from the Markdown directories listed in `MEMORY_DIRS`.

## Automatic retraining

`auto_retrain.py` evaluates feedback written by `training_guide.py`. When the
number of new intents exceeds the `RETRAIN_THRESHOLD` value it triggers the
fine-tuning routine via the local LLM API. Run it manually with:

```bash
python auto_retrain.py --run
```

This prints novelty and coherence scores and initiates fine-tuning when the
defined thresholds are met.
