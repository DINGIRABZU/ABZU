from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
README_OPERATOR = REPO_ROOT / "README_OPERATOR.md"
RECOVERY_PLAYBOOK = REPO_ROOT / "docs" / "recovery_playbook.md"


def test_readme_operator_links_connector_guidance() -> None:
    text = README_OPERATOR.read_text(encoding="utf-8")
    assert "docs/communication_interfaces.md#chakra-tagged-signals" in text


def test_recovery_playbook_links_connector_guidance() -> None:
    text = RECOVERY_PLAYBOOK.read_text(encoding="utf-8")
    assert "communication_interfaces.md#recovery-flows" in text
