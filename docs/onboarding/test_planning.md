# Test Planning Guide

Instructions for opening a "Test Plan" issue to coordinate tests across chakras and maintain coverage goals.

## Filing a Test Plan Issue

1. Open a new issue using the **Test Plan** template and apply the `test-plan` label.
2. Link the issue to the feature or bug it supports and to any related pull requests.
3. Include contact information for the owner responsible for executing the plan.

## Define the Scope

- Describe the features, modules, and scenarios that require validation.
- Note any out-of-scope areas to prevent redundant effort.
- Reference companion documents or specifications when available.

## Declare the Chakra

- Identify the chakra layer most affected by the work (e.g., root, sacral, solar plexus, heart, throat, third eye, crown).
- Use one chakra per issue to keep responsibilities clear.
- Align test fixtures and data to the chakra's responsibilities.

## Set Coverage Goals

- Record the current test coverage for the affected modules.
- State the target coverage percentage and the methods used to achieve it.
- Aim for at least 90% coverage for touched modules while maintaining the repository baseline.
- Update `component_index.json` and related dashboards when coverage goals are met.

## Checklist

- [ ] Issue links to related work and pull requests
- [ ] Scope and exclusions documented
- [ ] Chakra explicitly stated
- [ ] Coverage goals defined and tracked
- [ ] Dashboard entries and component index updated when complete
