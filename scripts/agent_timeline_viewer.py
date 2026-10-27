"""
agent_timeline_viewer.py

Assignment 6: Observability (part 2 - read the log back).

Reads run_log.jsonl (written by agent_observability.py) and prints
a readable timeline of one run - the same idea as a tracing UI, just as
plain text.

Run agent_observability.py FIRST, then run this.
Run with: python agent_timeline_viewer.py
"""

import json
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parent.parent          # the lab root, so paths work from any folder (IDE or terminal)
LOG_PATH = LAB_DIR / "logs" / "run_log.jsonl"


def load_events(path: str) -> list[dict]:
    """Reads the JSONL log: one event dict per non-empty line, in file order."""
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def print_timeline(events: list[dict]) -> None:
    """Prints one numbered line per event, e.g.
      1. [llm_call]  842ms  -> "..."
      2. [tool_call] 3ms    add({'a': 15, 'b': 27}) -> "42.0"
    """
    total_ms = 0.0
    for i, e in enumerate(events, start=1):
        ms = f"{e['duration_ms']:.0f}ms"
        total_ms += e["duration_ms"]
        if e["type"] == "llm_call":
            print(f"{i:>2}. [llm_call]  {ms:<8} -> \"{e['reply_preview']}\"")
        elif e["type"] == "tool_call":
            print(f"{i:>2}. [tool_call] {ms:<8} {e['tool']}({e['args']}) -> \"{e['result_preview']}\"")
        else:
            print(f"{i:>2}. [{e['type']}] {ms}")       # unknown event type: still show it
    print(f"\nTotal: {total_ms / 1000:.1f}s")


if __name__ == "__main__":
    events = load_events(LOG_PATH)
    print(f"{len(events)} events in this run:\n")
    print_timeline(events)
