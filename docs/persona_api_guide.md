# Persona API Guide

This guide walks developers through the persona utilities that power Albedo
interactions.  It shows how to update trust scores, compose messages and adjust
configuration files.

## Updating trust and state

Use :func:`agents.albedo.trust.update_trust` to record the outcome of an
interaction.  The function returns the updated trust magnitude along with the
current alchemical state.

```python
from agents.albedo.trust import update_trust

magnitude, state = update_trust("Ainz", "positive")
print(magnitude, state)
```

Trust values start from the baselines defined in
``memory/trust_registry.py`` and range from ``Magnitude.ZERO`` to
``Magnitude.TEN``.  The associated state is computed with the
:class:`albedo.state_machine.AlbedoStateMachine`.

## Composing persona messages

After updating trust you can build a reply using the messaging helpers.
``compose_message_nazarick`` formats lines for allies while
``compose_message_rival`` handles rivals:

```python
from agents.albedo.messaging import compose_message_nazarick
from agents.albedo.trust import update_trust

mag, state = update_trust("Ainz", "positive")
print(compose_message_nazarick("Ainz", state, mag))
```

The helpers load templates from YAML files in ``agents/albedo``.  Modify the
``nazarick_templates.yaml`` and ``rival_templates.yaml`` files to customise
rank mappings and message text.

## CLI demo

A small demonstration utility is provided at
``scripts/albedo_demo.py``.  It simulates a dialogue cycle by updating the
trust score and emitting the corresponding message:

```bash
python scripts/albedo_demo.py Ainz positive
python scripts/albedo_demo.py Shalltear negative --rival
```

## Configuration and logs

Template files reside beside the messaging module and are reloaded at runtime.
Dialogue interactions are appended to ``logs/albedo_interactions.jsonl``.  Delete
this file to reset the in-memory trust tracker.

Set the ``PYTHONPATH`` to the repository root when using the modules directly:

```bash
export PYTHONPATH=.
```

The persona APIs only depend on ``PyYAML`` and ``jsonschema`` which are included
in the base development requirements.
