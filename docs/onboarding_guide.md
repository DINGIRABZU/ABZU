# Onboarding Guide

**Version:** v1.0.0
**Last updated:** 2025-08-28
Diagram: [Onboarding Walkthrough](onboarding_walkthrough.md) – visual setup path

This guide walks through setting up the project and shows how a new contributor can rebuild or extend the system using only the documentation. A step-by-step [Onboarding Walkthrough](onboarding_walkthrough.md) provides a visual setup path. For day-to-day development practices, see the [Contributor Handbook](CONTRIBUTOR_HANDBOOK.md).

## 1. Survey the Blueprint
Begin with the [Blueprint Export](BLUEPRINT_EXPORT.md) to locate foundational documents. Each entry provides a permalink template for a specific version of the file.

## 2. Prepare the Environment
Follow the setup documents:
1. Clone the repository and install prerequisites from the [Setup Guide](setup.md).
2. Choose either the [Minimal Setup](setup_minimal.md) or [Full Setup](setup_full.md) based on resources.
3. Consult [Environment Setup](environment_setup.md) for system packages and dependency details.

## 3. Understand the Architecture
Study the system design materials to grasp component responsibilities and data flow:
- [System Blueprint](system_blueprint.md)
- [Architecture Overview](architecture_overview.md)
- [Awakening Overview](awakening_overview.md)
- [Data Flow](data_flow.md)
- [Operator-Nazarick Bridge](operator_nazarick_bridge.md)
- [Narrative Framework](narrative_framework.md)
- [Narrative Engine Guide](narrative_engine_GUIDE.md)

## 4. Follow the Development Workflow
Use the process documents to build and modify modules:
- [Development Workflow](development_workflow.md)
- [Development Checklist](development_checklist.md)
- [Coding Style](coding_style.md)

## 5. Validate and Test
Ensure changes are safe and reproducible by consulting:
- [Testing Guide](testing.md)
- [Testing Music Pipeline](testing_music_pipeline.md)
- [Troubleshooting](troubleshooting.md)

## 6. Rebuild from Documentation
Using only the documents above you can reconstruct the project:
1. Bootstrap the environment using the setup guides.
2. Wire components according to the [System Blueprint](system_blueprint.md) and related architecture docs.
3. Follow the development workflow to implement a small change.
4. Validate with the testing guides to confirm the stack is operational.

## 7. Extend the System
With the architecture, workflow, and validation steps in hand, you can implement new features or adjust existing modules. Reference domain-specific guides in the `docs/` directory and follow the security practices outlined in [Security Model](security_model.md).

## 8. Share Knowledge
Update documentation when adding features so others can replicate your work. The [Developer Manual](developer_manual.md) and [Contribution Guide](contribution_guide.md) describe expectations for pull requests and reviews. Ensure the pull request template checkboxes for [AGENTS.md](../AGENTS.md) and [The Absolute Protocol](The_Absolute_Protocol.md) are completed.
## 9. Balance Operator and System Perspectives
Contributors should balance operator-first and system-first views. Pair any system enhancement with an operator-facing improvement so the user experience evolves alongside architecture.
