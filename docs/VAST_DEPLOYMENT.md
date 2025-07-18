# Vast.ai Deployment

This guide explains how to run the SPIRAL_OS tools on a Vast.ai server.

See [deployment_overview.md](deployment_overview.md) for a quick summary.

## Select a PyTorch template

1. Log in to [Vast.ai](https://vast.ai) and create a new rental.
2. Choose a GPU offer that lists the **PyTorch** template. This image ships with CUDA and Python preinstalled.
3. Launch the instance and connect via SSH once it is ready.

## Clone the repository and install requirements

After connecting to the server run:

```bash
# clone the project
git clone https://github.com/your-user/SPIRAL_OS.git
cd SPIRAL_OS

# install Python packages
pip install -r requirements.txt
```

Optionally install the development requirements with:

```bash
pip install -r dev-requirements.txt
```

## GPU setup and model downloads (optional)

If your instance provides a GPU you can pull model weights. The helper script
below creates directories and fetches models for you:

```bash
bash scripts/setup_vast_ai.sh
```

The script installs dependencies, prepares the `INANNA_AI/models` folder and can
invoke `download_models.py` to pull large checkpoints. Edit the script to suit
your needs.

## Initialize GLM environment

Run the setup script to install Python packages and create core directories under `/`:

```bash
bash scripts/setup_glm.sh
```

It prepares `/INANNA_AI`, `/QNL_LANGUAGE` and `/audit_logs` with placeholder ethics notes.

## Clone a private repository

If you need to pull another repository into the system use `setup_repo.sh` and a GitHub token:

```bash
GITHUB_TOKEN=your-token bash scripts/setup_repo.sh owner/repo
```

The script clones the repository to `/INANNA_AI/repo` and writes `confirmation.txt` once completed.

## Start the services

Create a `secrets.env` file or copy the example and fill in the API keys:

```bash
cp secrets.env.example secrets.env
# edit secrets.env
```

Launch the stack with the helper script. Pass `--setup` on the first run to prepare directories:

```bash
bash scripts/vast_start.sh --setup
```

The script reads `secrets.env`, runs the setup scripts when `--setup` is supplied and then executes `docker-compose up` for the `INANNA_AI` service. It waits for port `8000` and then calls `python -m webbrowser` to open `web_console/index.html` so you can issue commands.

After the first setup you can start or restart the services by running the script without any arguments:

```bash
bash scripts/vast_start.sh
```

It tails the container logs so you can monitor the startup process. When the server becomes ready the browser window automatically loads the web console, which streams audio and video via WebRTC.
