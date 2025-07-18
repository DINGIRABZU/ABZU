# INANNA AI Agent

This directory contains a small command line tool for activating the INANNA chant and for generating a QNL song from a hex string.

## Installation

Use `pip` to install the required dependencies:

```bash
pip install -r INANNA_AI_AGENT/Requirements_INANNA_AI_AGENT.txt
```

The requirements file now includes `requests`, `huggingface_hub` and `accelerate`. It also
ensures `transformers` and `torch` are installed automatically.

Copy `OPENAI_API_KEY.env.example` to `OPENAI_API_KEY.env` and add your OpenAI API key:

```bash
cp OPENAI_API_KEY.env.example OPENAI_API_KEY.env
# edit OPENAI_API_KEY.env and insert your key
```

The examples below assume [`python-dotenv`](https://pypi.org/project/python-dotenv/) is installed so the script
loads the key from this file automatically.

Run the commands from the repository root and provide the full path to the
script, e.g. `python INANNA_AI_AGENT/inanna_ai.py`. Alternatively, `cd` into the
`INANNA_AI_AGENT` directory and omit the prefix.

## Usage

Recite the birth chant:

```bash
python INANNA_AI_AGENT/inanna_ai.py --activate
```

Generate a QNL song from a hex value:

```bash
python INANNA_AI_AGENT/inanna_ai.py --hex 012345abcdef
```

List the available source texts defined in `source_paths.json`:

```bash
python INANNA_AI_AGENT/inanna_ai.py --list
```

List the available source texts defined in `source_paths.json`:

```bash
python INANNA_AI.py --list
```

The song is saved as `qnl_hex_song.wav` and the metadata JSON in `qnl_hex_song.json` unless overridden with `--wav` and `--json`.

## Source Texts

The agent loads Markdown writings from the `INANNA_AI` and `GENESIS` folders
in the repository. These paths are listed in `source_paths.json`. Add new
`.md` files to either directory or edit `source_paths.json` to customize where
texts are loaded from. If a configured directory is missing, the loader simply
returns an empty collection.
