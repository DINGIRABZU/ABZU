# Troubleshooting

This guide addresses frequent setup problems, driver issues, and environment pitfalls.
Refer to [installation](installation.md) for the full setup procedure.

## Common installation errors

- **Outdated tools** – Upgrade the Python installer and package manager:
  ```bash
  python -m pip install --upgrade pip
  ```
- **Missing dependencies** – Install runtime packages from the lock file and optional
  development tools via [scripts/install_test_deps.sh](../scripts/install_test_deps.sh):
  ```bash
  pip install -r requirements.lock
  pip install -r dev-requirements.txt
  ./scripts/install_test_deps.sh
  ```
- **Model downloads failing** – Use [download_models.py](../download_models.py) to fetch
  pretrained weights and log progress to `logs/model_audit.log`:
  ```bash
  python download_models.py glm41v_9b --int8
  ```

## Missing drivers

- **GPU not detected** – Verify the driver and CUDA toolkit:
  ```bash
  nvidia-smi
  ```
  Install or update the vendor drivers if the command reports "not found".
- **Audio utilities absent** – Many tools rely on `ffmpeg` and `sox`. Confirm their
  presence with the validator in [env_validation.py](../env_validation.py):
  ```bash
  python -c "from env_validation import check_audio_binaries; check_audio_binaries()"
  ```

## Environment issues

- **Unset variables** – Validate required keys such as `OPENAI_API_KEY` with:
  ```bash
  python -c "from env_validation import check_required; check_required(['OPENAI_API_KEY'])"
  ```
- **Missing binaries** – Ensure external programs like `git` or `curl` are on `PATH`:
  ```bash
  python -c "from env_validation import check_required_binaries; check_required_binaries(['git','curl'])"
  ```

If problems persist, run the bootstrap script
[scripts/bootstrap.py](../scripts/bootstrap.py) to re-check the environment and
reproduce the error message:

```bash
python scripts/bootstrap.py
```

## Dependency check

Verify that core modules import correctly and optional packages are available:

```bash
python scripts/dependency_check.py
```

- `❌` indicates a component failed to import.
- `⚠️` means optional modules such as FAISS or OmegaConf are missing. Install them with:

```bash
pip install faiss-cpu omegaconf
```

Re-run the checker until all components report `✅`.
