# nodus-extension Design Doc 05 — Nodus Language Bindings

**Doc:** 05-bindings.md  **Status:** Complete — 2026-05-30
**Decisions grounded:** D1

## Host function prefix

Host functions use `_ext_` (underscore prefix) to avoid colliding with Nodus builtins.
The .nd wrappers (`ext_load`, `ext_list`, `ext_invoke`, `ext_describe`) call `_ext_*` internally.

This is the same pattern established by nodus-memory (`nm_*` prefix → `recall_from` wrappers).

## Critical Nodus language lesson

Nodus functions do NOT implicitly return the last expression result when the last statement
is a host function call. Wrappers in `index.nd` must use explicit `return`:

```nodus
fn ext_load(path) {
  return _ext_load(path)   ← "return" required; without it → nil
}
```

## attach_to_runtime pattern

```python
from nodus_extension import ExtensionRegistry, attach_to_runtime
from nodus import NodusRuntime

registry = ExtensionRegistry()
runtime = NodusRuntime(timeout_ms=None)  # None required for long-lived usage
attach_to_runtime(runtime, registry)
```

After this, Nodus scripts can `import "nodus-extension"` and use `ext_load`, `ext_invoke`, etc.

## ext_invoke JSON contract

`ext_invoke(name, tool, args_json)` takes args as a JSON string (not a Nodus map) because
the Nodus script layer cannot construct typed maps that survive the host boundary without
serialization. The caller must `json.dumps()` their args:

```nodus
let r = ext_invoke("myapp.ext", "myapp.greet", "{}")
```

The Python binding calls `json.loads(args_json)` before routing to `registry.invoke()`.
