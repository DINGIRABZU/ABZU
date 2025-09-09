# Security Model

This guide highlights major threat surfaces in the project and the steps
used to reduce risk.

## Threat Surfaces
- **Source code and dependencies** – third‑party packages or injected code may
  introduce vulnerabilities.
- **Secrets management** – API keys and credentials stored improperly can leak
  through version control or logs.
- **Command execution** – modules that spawn subprocesses can be abused if
  inputs are not sanitized.
- **Network interfaces** – exposed HTTP endpoints may be targeted for
  unauthorized access or denial‑of‑service attacks.

## Mitigation Steps
- Pin dependencies and scan the repository with
  `pre-commit run bandit --all-files` in CI to detect high-severity,
  high-confidence issues.
- Remediate findings by fixing the code or, when a warning is unavoidable,
  adding an inline `# nosec` comment with an explanation.
- Keep secrets in `secrets.env`, never commit them to git, and rotate tokens
  regularly.
- Avoid `shell=True` when invoking subprocesses and validate all external
  inputs.
- Require authentication for network services and restrict ports to trusted
  networks.
