# nodus-extension

> **Status:** v0.1.0 — published on [PyPI](https://pypi.org/project/nodus-extension/).

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

v0.1.0 — published on [PyPI](https://pypi.org/project/nodus-extension/). v0.1 ships subprocess sandbox (insecure-dev tier).
OCI container and VM tiers are v0.2+.

---

## Install

```bash
pip install nodus-extension
```

Requires `nodus-lang>=4.0.0` and `pydantic>=2.0`.

---

## ExtensionRegistry

```python
from nodus_extension import ExtensionRegistry

registry = ExtensionRegistry()
registry.load("/path/to/my-extension")   # reads nodus-extension.json
registry.load("/path/to/another-ext")

ext = registry.get("myapp.my-extension")   # ExtensionHost | None
all_exts = registry.list_all()             # list[ExtensionHost]
registry.unload("myapp.my-extension")
```

---

## ExtensionHost

```python
host = registry.get("myapp.my-extension")

host.name           # "myapp.my-extension"
host.manifest       # ExtensionManifest
host.gate           # CapabilityGate

result = host.invoke("myapp.greet", '{"name": "Alice"}')
# result is the JSON-decoded return value from the extension
```

`invoke` takes args as a JSON string — not a dict. The extension runs in
a subprocess; the args are serialized over NDJSON IPC.

---

## Capabilities

```python
from nodus_extension import Capability, CapabilityGate

gate = CapabilityGate({"tool.invoke", "memory.read"})
gate.has(Capability.TOOL_INVOKE)    # True
gate.require(Capability.NETWORK_OUTBOUND)  # raises CapabilityError
```

---

## Provenance

```python
from nodus_extension import Provenance, Origin, TrustClass, OwnerClass

prov = Provenance(
    origin=Origin.LOCAL,
    trust_class=TrustClass.DEV,
    owner_class=OwnerClass.PERSONAL,
)
```

---

## Error types

| Error | When raised |
|---|---|
| `ManifestError` | Invalid or missing `nodus-extension.json` |
| `CapabilityError` | Extension attempts an undeclared capability |
| `SandboxError` | Subprocess failed to start or exited unexpectedly |
| `AbiError` | `abi_version` mismatch |
| `RegistryError` | Duplicate or unknown extension name |
| `InvokeError` | Extension returned an error response |
| `TimeoutError` | Invocation exceeded per-invoke timeout |

---

## Development

```bash
pip install -e ".[dev]"
PYTHONPATH=src pytest tests/ -q
```

---

## Known limitations (v0.1)

- **Subprocess sandbox only.** OCI container and VM isolation tiers are v0.2+.
- `ext_invoke` args are a **JSON string**, not a Nodus map.
- Extensions must declare `"tool.invoke"` capability to register tools.
