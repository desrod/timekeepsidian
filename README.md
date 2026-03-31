# keepsidian

A small command-line utility for injecting [TimeKeep](https://github.com/Tarkin25/obsidian-timekeep) timer entries directly into your Obsidian daily notes from the terminal — no mouse required.

## What it does

If you use the TimeKeep plugin in Obsidian and keep a daily note, this script lets you start a named timer from the command line. It finds today's note, locates the `timekeep` code block, stops any currently running timer, and appends a new running entry with whatever name you pass in. Handy when you're already in a terminal and don't want to context-switch just to click a button.

## Requirements

- Python 3.9+
- Obsidian with the [TimeKeep plugin](https://github.com/Tarkin25/obsidian-timekeep) installed
- A daily note that contains a `timekeep` fenced code block

## Setup

No external dependencies — just the standard library.

Clone the repo and set the `VAULT_PATH` environment variable to point at your Obsidian vault:

```bash
export VAULT_PATH="/path/to/your/obsidian-notes"
```

You can drop that in your `.bashrc` / `.zshrc` so you don't have to think about it.

## Usage

```bash
python3 inject-time.py "Task name here"
```

If you don't pass a name it defaults to `New Task`.

### Example

```bash
python3 inject-time.py "Code review"
# Started timer 'Code review' in /path/to/vault/Daily Notes/2026-03-30-Monday.md
```

Any timer that was already running in the block gets stopped at the same timestamp the new one starts, so your time accounting stays clean.

## How it works

The script reads your daily note, finds the `timekeep` JSON block using a regex, parses the JSON, closes any open entry, and appends a new one. It then writes the file back. Straightforward file manipulation — nothing fancy, nothing that touches the network.

## Notes

- Timestamps are always UTC, which is what the TimeKeep plugin expects.
- The script will exit with an error if the note file doesn't exist or if no `timekeep` block is found.
- The `VAULT_PATH` defaults to `/Users/desrod/Documents/obsidian-notes` if the environment variable isn't set — you'll want to change that default in the script if you're sharing this with others.

## License

Do whatever you want with it.
