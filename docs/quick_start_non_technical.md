# Quick Start Guide (Non-Technical)

Follow these steps to get the system running with minimal setup.

1. Copy `secrets.env.template` to `secrets.env` and provide the required tokens.
   To enable local servant models define `SERVANT_MODELS`, for example:

   ```env
   SERVANT_MODELS=deepseek=http://localhost:8002,mistral=http://localhost:8003,kimi_k2=http://localhost:8010
   ```
2. Run `bash scripts/easy_setup.sh` to download models and install the core dependencies.
3. Launch the local environment with `bash scripts/start_local.sh`.
4. *(Optional)* For a cloud deployment on Vast.ai, run `bash scripts/vast_start.sh --setup`.

These commands should be executed from the project root directory.
