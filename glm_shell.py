from __future__ import annotations

"""Send shell commands to the Crown GLM endpoint.

Usage:
    python glm_shell.py "<command>"
"""

import argparse

from crown_config import require, settings

from INANNA_AI.glm_integration import GLMIntegration
from init_crown_agent import initialize_crown


def send_command(command: str) -> str:
    """Return GLM response for ``command`` sent as a shell instruction.

    Set ``GLM_SHELL_URL`` and ``GLM_SHELL_KEY`` to target a dedicated
    shell endpoint. Defaults to the main Crown configuration.
    """
    url = settings.glm_shell_url
    key = settings.glm_shell_key
    if url or key:
        require("glm_shell_url", "glm_shell_key")
        glm = GLMIntegration(endpoint=url, api_key=key)
    else:
        glm = initialize_crown()
    prompt = f"[shell]{command}"
    return glm.complete(prompt)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="glm_shell")
    parser.add_argument("command", help="Shell command to execute")
    args = parser.parse_args(argv)
    print(send_command(args.command))


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
