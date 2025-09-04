import re
import sys
from pathlib import Path

CHECKLIST_PATH = Path("docs/absolute_protocol_checklist.md")

content = CHECKLIST_PATH.read_text(encoding="utf-8")
unchecked = re.findall(r"- \[ \] .+", content)
if unchecked:
    print("Unchecked items in absolute_protocol_checklist.md:")
    for item in unchecked:
        print(item)
    sys.exit(1)
print("All checklist items are marked complete.")
