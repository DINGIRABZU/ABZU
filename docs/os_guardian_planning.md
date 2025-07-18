# OS Guardian Planning

The planning module converts natural language instructions into a sequence of
calls to the perception and action components. It stores previous plans in a
vector memory so repeated requests share context.

## Examples

```python
from os_guardian.planning import GuardianPlanner

planner = GuardianPlanner()
steps = planner.plan("Open the browser and search for Spiral OS")
for step in steps:
    print(step)

# Incorporate perception feedback
steps = planner.interactive_plan(
    "Click the highlighted result",
    perception_feedback="Found a button labelled 'Spiral OS'"
)
```
