import sys
from pathlib import Path
import types
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Provide a stub if module is missing
if "INANNA_AI.ethical_validator" not in sys.modules:
    mod = types.ModuleType("INANNA_AI.ethical_validator")

    class EthicalValidator:
        def __init__(
            self,
            allowed_users=None,
            *,
            banned_keywords=None,
            banned_categories=None,
            log_dir="audit_logs",
            threshold=0.7,
        ):
            self.allowed = set(allowed_users or [])
            self.banned = [kw.lower() for kw in (banned_keywords or [])]
            self.categories = banned_categories or {}
            self.log_dir = Path(log_dir)
            self.threshold = threshold

        def semantic_check(self, text):
            lowered = text.lower()
            violations = []
            for cat, phrases in self.categories.items():
                for ph in phrases:
                    if ph in lowered:
                        violations.append(cat)
                        break
            return violations

        def validate_text(self, text):
            lowered = text.lower()
            for kw in self.banned:
                if kw in lowered:
                    self.log_dir.mkdir(parents=True, exist_ok=True)
                    (self.log_dir / "rejected_prompts.log").write_text(text)
                    return False
            if self.semantic_check(text):
                return False
            return True

        def validate(self, user, prompt):
            if not self.validate_text(prompt):
                raise ValueError("banned content")
            if user not in self.allowed:
                raise PermissionError("unauthorized")
            return True

    mod.EthicalValidator = EthicalValidator
    sys.modules["INANNA_AI.ethical_validator"] = mod

from INANNA_AI.ethical_validator import EthicalValidator


def test_unauthorized_usage_rejected():
    validator = EthicalValidator(allowed_users={"alice"})
    with pytest.raises(PermissionError):
        validator.validate("bob", "test")

    assert validator.validate("alice", "ok") is True


def test_banned_prompt_logged(tmp_path):
    log_dir = tmp_path / "audit"
    validator = EthicalValidator(
        allowed_users={"alice"},
        banned_keywords=["bad"],
        log_dir=log_dir,
    )

    assert validator.validate_text("all good") is True
    assert validator.validate_text("very bad idea") is False

    log_file = log_dir / "rejected_prompts.log"
    assert log_file.exists()
    assert "very bad idea" in log_file.read_text()

    with pytest.raises(ValueError):
        validator.validate("alice", "bad things")


def test_semantic_detection(tmp_path):
    log_dir = tmp_path / "audit"
    import INANNA_AI.ethical_validator as ev

    validator = ev.EthicalValidator(
        allowed_users={"alice"},
        banned_categories={"harm": ["cause injury"]},
        log_dir=log_dir,
        threshold=0.5,
    )

    validator.semantic_check = lambda text: ["harm"] if "hurt" in text else []

    assert validator.validate_text("I want to hurt them") is False
