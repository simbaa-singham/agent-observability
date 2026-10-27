# agent-observability

Agent observability from scratch (assignment 6): raw Ollama API (`qwen2.5:7b`), no framework.

| Script | What it does |
|---|---|
| `agent_observability.py` | Runs the agent and writes one JSON line per step to `logs/run_log.jsonl` |
| `agent_timeline_viewer.py` | Reads `logs/run_log.jsonl` and prints the run's timeline (run `agent_observability.py` first) |

Run every script from the `scripts` folder. Assignment notes: `docs/Assignment_6_Observability.md`.

## Before running
- Ollama running with `qwen2.5:7b`.
- `pip install -r requirements.txt`
