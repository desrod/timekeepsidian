#!/usr/bin/env python3

import datetime
import json
import os
import re
import sys
from datetime import timezone

# You will need to adjust this naming convention, my notes are
# named '2026-03-29-Sunday.md' for example
VAULT_PATH = os.environ.get("VAULT_PATH", "~/Documents/obsidian-notes")
TODAY      = datetime.date.today().strftime("%Y-%m-%d-%A")
NOTE       = os.path.join(VAULT_PATH, "Daily Notes", f"{TODAY}.md")

ENTRY_NAME = sys.argv[1] if len(sys.argv) > 1 else "New Task"

if not os.path.exists(NOTE):
    print(f"Note not found: {NOTE}")
    sys.exit(1)

with open(NOTE, "r") as f:
    content = f.read()

pattern = r"(```timekeep[ \t]*\r?\n)(.*?)(\r?\n```)"
match   = re.search(pattern, content, re.DOTALL)

if not match:
    print(f"No timekeep block found in {NOTE}")
    for line in content.splitlines():
        if "timekeep" in line:
            print(repr(line))
    sys.exit(1)

data    = json.loads(match.group(2))
now_iso = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

# Belt and suspenders, stop any running timers before continuing
for entry in data["entries"]:
    if entry.get("startTime") is not None and entry.get("endTime") is None:
        entry["endTime"] = now_iso

# Add new running entry to existing TimeKeep block
data["entries"].append(
    {"name": ENTRY_NAME, "startTime": now_iso, "endTime": None, "subEntries": None}
)

new_block   = match.group(1) + json.dumps(data) + match.group(3)
new_content = content[: match.start()] + new_block + content[match.end() :]

with open(NOTE, "w") as f:
    f.write(new_content)

print(f"Started timer '{ENTRY_NAME}' in {NOTE}")
