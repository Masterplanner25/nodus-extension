# nodus-extension

Typed, versioned, sandboxed extension framework for Nodus agents.

Allows platform operators to let third-party developers extend a Nodus application
with typed, versioned, sandboxed plugins — registering agent tools without access
to host runtime internals.

## Quick start — host operator

```python
from nodus import NodusRuntime
from nodus_extension import ExtensionRegistry, attach_to_runtime

registry = ExtensionRegistry()
registry.load("/path/to/my-extension")

runtime = NodusRuntime(timeout_ms=None)
attach_to_runtime(runtime, registry)

# Scripts can now load and invoke extensions
result = runtime.run_source('''
import "nodus-extension"
let result = ext_invoke("myapp.my-extension", "myapp.greet", "{\"name\": \"Alice\"}")
print(result)
''')
```

## Quick start — extension developer

Create a directory with `nodus-extension.json` and `extension.py`:

```json
{
  "name": "myapp.greet-extension",
  "version": "1.0.0",
  "description": "Greets people",
  "abi_version": "1",
  "capabilities": ["tool.invoke"],
  "surfaces": {
    "tools": [{"name": "myapp.greet", "description": "Greet by name"}]
  }
}
```

```python
from nodus_extension.worker import register_tool, run_loop

register_tool("myapp.greet", lambda args: f"Hello, {args['name']}!")
run_loop()
```

## Capabilities

| Capability | Grants |
|-----------|--------|
| `filesystem.read` | read_file, list_dir, exists |
| `filesystem.write` | write_file, append_file, mkdir |
| `network.outbound` | std:http outbound calls |
| `subprocess.run` | std:subprocess |
| `tool.invoke` | invoke tools in host registry |
| `memory.read` | read from host memory store |
| `memory.write` | write to host memory store |

## Status

v0.1.0 — PREPARED, NOT RELEASED. v0.1 ships subprocess sandbox (insecure-dev tier).
OCI container and VM tiers are v0.2+.
