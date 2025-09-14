# External Contributor Onboarding

New contributors should complete the standard [Onboarding Checklist](README.md)
and ensure the following before submitting pull requests:

1. Clone the repository and run `python docs/onboarding/wizard.py`.
2. Confirm required documents in `onboarding_confirm.yml` and answer
   `onboarding_quiz.yml` questions.
3. Install development dependencies with `pip install -r dev-requirements.txt`.
4. Run `pre-commit install` to enable formatting and validation hooks.
5. Execute `pre-commit run --files <changed_files>` and
   `pre-commit run verify-onboarding-refs` before committing.

### Doctrine References
- [system_blueprint.md](../system_blueprint.md)
- [The_Absolute_Protocol.md](../The_Absolute_Protocol.md)
