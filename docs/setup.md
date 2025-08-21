# Environment Setup

This guide lists the system packages and environment variables required to run the project.

## Required Packages

The [scripts/check_requirements.sh](../scripts/check_requirements.sh) script expects the following commands to be available:

- docker
- nc
- sox
- ffmpeg
- curl
- jq
- wget
- aria2c

### Debian/Ubuntu

```bash
sudo apt-get update
sudo apt-get install -y docker.io netcat-openbsd sox ffmpeg curl jq wget aria2
```

### macOS

```bash
brew install docker netcat sox ffmpeg curl jq wget aria2
```

## Environment Variables

Create a `secrets.env` file (copy from `secrets.env.template`) and define:

```bash
HF_TOKEN=<your Hugging Face token>
GLM_API_URL=<GLM endpoint>
GLM_API_KEY=<API key>
```

## Validate Setup

Run the following script from the repository root to verify the configuration:

```bash
scripts/check_requirements.sh
```

The script loads `secrets.env` and confirms that all required commands and variables are present.

