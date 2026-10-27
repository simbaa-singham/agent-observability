"""
agent_observability.py

Assignment 6: Observability (part 1 - instrument the harness).

Same harness shape as assignment 1, but call_llm and run_tool are now
wrapped with timing + structured logging: every call writes one JSON
line to run_log.jsonl (timestamp, duration, what happened). This is
exactly what LangSmith-style tracing tools do under the hood - you're
building the plumbing by hand once so it's not a black box.

See agent_timeline_viewer.py to read the log back as a readable timeline.

Run with: python agent_observability.py
"""

import json
import time
from datetime import datetime
from pathlib import Path
import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b"
LAB_DIR = Path(__file__).resolve().parent.parent          # the lab root, so paths work from any folder (IDE or terminal)
LOG_PATH = LAB_DIR / "logs" / "run_log.jsonl"

SYSTEM_PROMPT = """You are a helpful assistant with access to tools.

Available tools:
- add(a, b): adds two numbers
- get_time(): returns the current time

If you need a tool to answer, respond with ONLY this JSON, nothing else:
{"tool": "<tool name>", "args": {<arguments>}}
Call one tool per reply; you will get its result before calling the next.

Once you have everything you need, respond in plain English - that is
the final answer shown to the user, not JSON."""


def add(a: float, b: float) -> float:
    return a + b


def get_time() -> str:
    return datetime.now().strftime("%H:%M:%S")


TOOLS = {
    "add": add,
    "get_time": get_time,
}


def log_event(event: dict) -> None:
    """Appends one JSON line to LOG_PATH (append mode, so one run builds up a single log)."""
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(event) + "\n")


def _call_llm_raw(messages: list[dict]) -> str:
    # given: the actual network call, unchanged from assignment 1
    response = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "messages": messages, "stream": False},
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


def call_llm_logged(messages: list[dict]) -> str:
    """Times the LLM call, logs it as an "llm_call" event, returns the reply."""
    start = time.perf_counter()                    # high-resolution timer, unaffected by clock changes
    reply = _call_llm_raw(messages)
    log_event({
        "type": "llm_call",
        "timestamp": datetime.now().isoformat(),
        "duration_ms": round((time.perf_counter() - start) * 1000, 1),
        "num_messages_in": len(messages),
        "reply_preview": reply[:80],
    })
    return reply


def parse_tool_call(text: str) -> dict | None:
    """Returns the first {"tool": ...} JSON object in the reply - models often add prose around it."""
    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(text, i)   # parses one JSON value starting at i, ignores the rest
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and "tool" in parsed:
            return parsed
    return None


def run_tool_logged(name: str, args: dict) -> str:
    """Times the tool call, logs it as a "tool_call" event (failures too), returns the result as text."""
    start = time.perf_counter()
    if name not in TOOLS:
        result = f"ERROR: unknown tool '{name}'"   # still logged below - failures matter most
    else:
        try:
            result = str(TOOLS[name](**args))      # **args unpacks {"a": 15, "b": 27} into a=15, b=27
        except Exception as e:                     # e.g. wrong argument names from the model
            result = f"ERROR: {type(e).__name__}: {e}"
    log_event({
        "type": "tool_call",
        "timestamp": datetime.now().isoformat(),
        "duration_ms": round((time.perf_counter() - start) * 1000, 1),
        "tool": name,
        "args": args,
        "result_preview": result[:80],
    })
    return result


def agent_loop(user_message: str, max_turns: int = 5) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    for _ in range(max_turns):
        reply = call_llm_logged(messages)
        tool_call = parse_tool_call(reply)

        if tool_call is None:
            return reply

        messages.append({"role": "assistant", "content": reply})
        result = run_tool_logged(tool_call["tool"], tool_call.get("args", {}))
        messages.append({"role": "user", "content": f"Tool result: {result}"})

    return "Gave up after too many turns."


if __name__ == "__main__":
    open(LOG_PATH, "w").close()  # start each run with a clean log file
    answer = agent_loop("What's 15 plus 27, and what time is it right now?")
    print(answer)
    print(f"\n(full trace written to {LOG_PATH} - run agent_timeline_viewer.py to view it)")
