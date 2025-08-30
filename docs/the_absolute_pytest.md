# The Absolute pytest

**Version:** 1.0.0

This guide codifies pytest practices for the ABZU project.

## Chakra-aligned test directories

Tests live under chakra-specific directories to mirror system layers:

- `tests/root/`
- `tests/sacral/`
- `tests/solar_plexus/`
- `tests/heart/`
- `tests/throat/`
- `tests/third_eye/`
- `tests/crown/`

## Test types

- **Unit** – isolated functions or classes.
- **Integration** – interactions between modules.
- **Smoke** – quick checks proving core functionality.
- **Regression** – ensure past defects stay fixed.
- **Environment** – validate external dependencies and runtime configuration.

## Metadata expectations

Each test module declares metadata for traceability:

- `test_id` – unique identifier.
- `component_id` – module or service under test.
- `coverage` – targeted coverage percentage.
- `status` – `active`, `deprecated`, or `experimental`.
- `issues` – linked tracking numbers.

## Commit process

Follow this sequence when adding or updating tests:

1. **Issue** – describe the problem or feature.
2. **Test** – implement or adjust tests.
3. **Coverage** – run coverage tools and update reports.
4. **AI review** – obtain feedback from review agents.
5. **Archive** – finalize in version control.

## References

- [Testing Guide](testing.md)
- [Documentation Index](INDEX.md)
