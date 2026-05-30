# nodus-extension Design Doc 03 — Sandbox Runner and IPC Protocol

**Doc:** 03-sandbox.md  **Status:** Complete — 2026-05-30
**Decisions grounded:** D6, D7

## Sandbox tiers

| Tier | Class | v0.1 | Description |
|------|-------|-------|-------------|
| 1 | `SubprocessRunner` | ✓ | Plain Python subprocess (insecure-dev) |
| 2 | `DockerRunner` | v0.2 | OCI container with resource limits |
| 3 | `VmRunner` | Deferred | Firecracker/gVisor strong isolation |

`SandboxRunner` ABC enables swap-in without API changes.

## NDJSON IPC Protocol (tier 1)

Host → Worker (one JSON line per message):
```
{"id": "uuid4", "op": "invoke", "name": "myapp.tool", "args": {...}}
{"op": "shutdown"}
```

Worker → Host:
```
{"id": "uuid4", "ok": true, "result": ...}
{"id": "uuid4", "ok": false, "error": "message"}
```

- Each line is one complete JSON object followed by `\n`
- `id` correlates request to response; non-matching responses are ignored
- Worker must flush stdout after each response (`stdout.flush()`)
- `shutdown` message has no id; worker exits the `run_loop()` cleanly

## Extension developer contract

`extension.py` in the extension root. Must import `nodus_extension.worker`:

```python
from nodus_extension.worker import register_tool, run_loop

def my_handler(args: dict) -> any:
    ...

register_tool("myapp.my_tool", my_handler)
run_loop()   # blocks until shutdown
```

`run_loop()` reads from stdin and writes to stdout. The host calls `runner.stop()`
which sends `{"op": "shutdown"}` and waits up to 2 seconds before killing.

## Timeout

Per-invoke timeout (`timeout_s`, default 30s). Implemented via a reader thread:
the main invoke thread joins the reader with `timeout_s`; if it doesn't complete,
`TimeoutError` is raised. The subprocess is not killed on timeout (the invoke thread
just gives up); subsequent invocations will fail with `SandboxError` if the subprocess
has hung. Caller should call `runner.stop()` after `TimeoutError`.
