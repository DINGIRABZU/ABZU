# Operator Onboarding

A guided walkthrough for composing and executing your first mission.

## Mission Builder

1. Open `web_console/mission_builder/index.html` in a browser.
2. Arrange blocks such as **Ignite**, **Query Memory**, and **Dispatch Agent** to describe your mission.
3. Click **Save & Run** to store the mission under `missions/` and dispatch it through the task orchestrator.

```mermaid
{{#include assets/mission_builder.mmd}}
```

The Mermaid source lives at [assets/mission_builder.mmd](assets/mission_builder.mmd).

## Game Dashboard Wizard

Visiting `web_console/game_dashboard/` presents an onboarding wizard after setup.
The wizard tracks progress in `localStorage` and guides you through mission creation
and execution.

```mermaid
{{#include assets/mission_wizard.mmd}}
```

The Mermaid source lives at [assets/mission_wizard.mmd](assets/mission_wizard.mmd).

Once both steps complete, the dashboard becomes fully interactive and streams events
from running agents.
