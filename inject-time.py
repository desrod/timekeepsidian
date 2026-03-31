#!/usr/bin/env python3

import argparse
import json
import os
import re
import sys

import pendulum


def load_daily_note_settings(vault_path):
    settings_path = os.path.join(vault_path, ".obsidian", "daily-notes.json")
    if not os.path.exists(settings_path):
        return "Daily Notes", "YYYY-MM-DD-dddd"
    with open(settings_path) as f:
        settings = json.load(f)
    return settings.get("folder", "Daily Notes"), settings.get(
        "format", "YYYY-MM-DD-dddd"
    )


parser = argparse.ArgumentParser(
    description="Inject a timekeep timer into today's Obsidian daily note."
)
action = parser.add_mutually_exclusive_group()
action.add_argument(
    "-p", "--pause", action="store_true", help="Pause the running timer"
)
action.add_argument(
    "-r",
    "--resume",
    nargs="?",
    const="",
    metavar="NAME",
    help="Resume the last paused timer, or a specific timer by exact name",
)
parser.add_argument(
    "-v",
    "--vault",
    metavar="PATH",
    help="Path to Obsidian vault (overrides $VAULT_PATH)",
)
parser.add_argument("name", nargs="?", default="New Task", help="Timer entry name")
args = parser.parse_args()

VAULT_PATH = args.vault or os.environ.get("VAULT_PATH")
if not VAULT_PATH:
    parser.error(
        "Vault path must be set via -v/--vault or the $VAULT_PATH environment variable"
    )

DAILY_FOLDER, DATE_FMT = load_daily_note_settings(VAULT_PATH)
TODAY = pendulum.now().format(DATE_FMT)
NOTE = os.path.join(VAULT_PATH, DAILY_FOLDER, f"{TODAY}.md")

if not os.path.exists(NOTE):
    print(f"Note not found: {NOTE}")
    sys.exit(1)

with open(NOTE, "r") as f:
    content = f.read()

pattern = r"(```timekeep[ \t]*\r?\n)(.*?)(\r?\n```)"
match = re.search(pattern, content, re.DOTALL)

if not match:
    print(f"No timekeep block found in {NOTE}")
    for line in content.splitlines():
        if "timekeep" in line:
            print(repr(line))
    sys.exit(1)

data = json.loads(match.group(2))
now_iso = pendulum.now("UTC").format("YYYY-MM-DDTHH:mm:ss.SSS[Z]")

# Find the running entry. For subEntry-based timers, close the running subEntry immediately
# since that's correct for every action. For simple entries, defer closing to each branch
# so -p can convert the entry rather than just stamping an endTime.
running = None
for entry in data["entries"]:
    if entry.get("subEntries"):
        for sub in entry["subEntries"]:
            if sub.get("startTime") and sub.get("endTime") is None:
                sub["endTime"] = now_iso
                running = entry
                break
    elif entry.get("startTime") and entry.get("endTime") is None:
        running = entry
        break

if args.pause:
    if not running:
        msg = "No running timer to pause"
    elif running.get("subEntries"):
        # Running subEntry was already closed above
        msg = f"Paused '{running['name']}'"
    else:
        # Convert simple entry → subEntry model to match TimeKeep's native format
        original_start = running["startTime"]
        running["startTime"] = None
        running["endTime"] = None
        running["subEntries"] = [
            {
                "name": "Part 1",
                "startTime": original_start,
                "endTime": now_iso,
                "subEntries": None,
            }
        ]
        msg = f"Paused '{running['name']}'"

elif args.resume is not None:
    # Close a simple running entry if one slipped through
    if running and not running.get("subEntries"):
        running["endTime"] = now_iso
    # Find the most recently paused subEntry-based timer (last subEntry has an endTime),
    # optionally filtered to an exact name when one was provided
    paused = next(
        (
            e
            for e in reversed(data["entries"])
            if e.get("subEntries")
            and e["subEntries"][-1].get("endTime")
            and e is not running
            and (not args.resume or e["name"] == args.resume)
        ),
        None,
    )
    if paused:
        n = len(paused["subEntries"]) + 1
        paused["subEntries"].append(
            {
                "name": f"Part {n}",
                "startTime": now_iso,
                "endTime": None,
                "subEntries": None,
            }
        )
        msg = f"Resumed '{paused['name']}'"
    else:
        # Fallback: no paused subEntry timer found
        if args.resume:
            # Named resume: convert the original simple entry in-place if it exists
            original = next(
                (
                    e
                    for e in data["entries"]
                    if e["name"] == args.resume
                    and e.get("startTime")
                    and e.get("endTime")
                ),
                None,
            )
            if original:
                original["subEntries"] = [
                    {
                        "name": "Part 1",
                        "startTime": original["startTime"],
                        "endTime": original["endTime"],
                        "subEntries": None,
                    },
                    {
                        "name": "Part 2",
                        "startTime": now_iso,
                        "endTime": None,
                        "subEntries": None,
                    },
                ]
                original["startTime"] = None
                original["endTime"] = None
                msg = f"Resumed '{original['name']}'"
            else:
                data["entries"].append(
                    {
                        "name": args.resume,
                        "startTime": now_iso,
                        "endTime": None,
                        "subEntries": None,
                    }
                )
                msg = f"Resumed '{args.resume}'"
        else:
            last = next(
                (e for e in reversed(data["entries"]) if e.get("endTime")), None
            )
            name = last["name"] if last else args.name
            data["entries"].append(
                {
                    "name": name,
                    "startTime": now_iso,
                    "endTime": None,
                    "subEntries": None,
                }
            )
            msg = f"Resumed '{name}'"

else:
    # Default: close simple running entry (subEntry-based was already closed above), start new
    if running and not running.get("subEntries"):
        running["endTime"] = now_iso
    data["entries"].append(
        {"name": args.name, "startTime": now_iso, "endTime": None, "subEntries": None}
    )
    msg = f"Started '{args.name}'"

new_block = match.group(1) + json.dumps(data) + match.group(3)
new_content = content[: match.start()] + new_block + content[match.end() :]

with open(NOTE, "w") as f:
    f.write(new_content)

print(f"{msg} in {NOTE}")
