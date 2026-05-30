"""Extension worker runtime.

Extension developers import this module in their extension.py:

    from nodus_extension.worker import register_tool, run_loop

    def my_handler(args: dict) -> str:
        return f"Hello, {args['name']}!"

    register_tool("myapp.greet", my_handler)
    run_loop()

The worker reads JSON requests from stdin and writes JSON responses to stdout.
Each line is one complete JSON object (NDJSON protocol).

Protocol (host → worker):
    {"id": "uuid", "op": "invoke", "name": "tool.name", "args": {...}}
    {"op": "shutdown"}

Protocol (worker → host):
    {"id": "uuid", "ok": true, "result": ...}
    {"id": "uuid", "ok": false, "error": "message"}
"""
from __future__ import annotations

import json
import sys
from typing import Any, Callable

_REGISTRY: dict[str, Callable[[dict[str, Any]], Any]] = {}


def register_tool(name: str, handler: Callable[[dict[str, Any]], Any]) -> None:
    """Register a tool in this worker process.

    Must be called before run_loop().
    """
    _REGISTRY[name] = handler


def run_loop(*, stdin=None, stdout=None) -> None:
    """Enter the stdin/stdout message loop. Blocks until shutdown message received."""
    _in = stdin if stdin is not None else sys.stdin
    _out = stdout if stdout is not None else sys.stdout

    for line in _in:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        op = msg.get("op")

        if op == "shutdown":
            break

        if op == "invoke":
            msg_id = msg.get("id", "")
            tool_name = msg.get("name", "")
            args = msg.get("args") or {}
            handler = _REGISTRY.get(tool_name)
            if handler is None:
                _send(_out, {"id": msg_id, "ok": False, "error": f"tool not found: {tool_name!r}"})
                continue
            try:
                result = handler(args)
                _send(_out, {"id": msg_id, "ok": True, "result": result})
            except Exception as exc:
                _send(_out, {"id": msg_id, "ok": False, "error": str(exc)})

        else:
            msg_id = msg.get("id", "")
            _send(_out, {"id": msg_id, "ok": False, "error": f"unknown op: {op!r}"})


def _send(out, obj: dict) -> None:
    out.write(json.dumps(obj) + "\n")
    out.flush()
