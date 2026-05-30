# nodus-extension Design Doc 01 — Manifest and ABI Surface Versioning

**Doc:** 01-manifest.md  **Status:** Complete — 2026-05-30
**Decisions grounded:** D2, D4, D5, D8

---

## A — Manifest Format

### A.1 File

`nodus-extension.json` in the extension root directory. JSON only (no YAML — avoids dep).

### A.2 Schema

```json
{
  "name":               "myapp.my-extension",
  "version":            "1.0.0",
  "description":        "Human-readable description",
  "abi_version":        "1",
  "min_nodus_version":  "4.0.0",
  "capabilities":       ["tool.invoke"],
  "provenance":         {"origin": "local", "trust_class": "dev", "owner_class": "personal"},
  "surfaces":           {"tools": [{...}]}
}
```

### A.3 Required fields

`name`, `version`, `description`. All others have defaults.

### A.4 abi_version semantics

`"1"` is the only supported value in v0.1. The manifest parser validates this first (before
full Pydantic validation) to give a clean `AbiError` with the actual version that was seen.

---

## B — ABI Surfaces

### B.1 v0.1: tool/v1alpha1

The only surface type in v0.1. Each tool surface declaration:

```json
{
  "name":        "myapp.summarize",
  "description": "Summarize text",
  "schema":      {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
  "version":     "v1alpha1"
}
```

Name must be dotted (regex: `^[a-z0-9_]+(\.[a-z0-9_]+)+$`). `schema` is optional JSON Schema.

### B.2 Deferred surfaces (v0.2+)

| Surface | What it enables | Blocker |
|---------|----------------|---------|
| `node/v1alpha1` | Custom flow nodes | Requires nodus-workflow |
| `webhook/v1alpha1` | Outbound webhooks | Requires HTTP server on extension side |
| `flow/v1alpha1` | Full flow definitions | Requires DAG compiler integration |
| `planner_backend/v1alpha1` | Planner backends | Requires agent framework |

---

## C — Capability Declaration

7 capabilities (D8 — allowlist model):

| String | Grants |
|--------|--------|
| `filesystem.read` | `read_file`, `list_dir`, `exists` |
| `filesystem.write` | `write_file`, `append_file`, `mkdir` |
| `network.outbound` | `std:http` outbound calls |
| `subprocess.run` | `std:subprocess` |
| `tool.invoke` | invoke tools in the host registry |
| `memory.read` | read from host memory store |
| `memory.write` | write to host memory store |

Unknown strings are rejected at manifest parse time (`ManifestError`), not at invocation time.
This ensures extensions cannot accidentally acquire capabilities through typos.

---

## D — Provenance

Three axes (D9 — informational in v0.1):

| Field | Values | Meaning |
|-------|--------|---------|
| `origin` | `local` / `registry` / `git` | Where the extension came from |
| `trust_class` | `dev` / `verified` / `trusted` | Operator-assigned trust tier |
| `owner_class` | `personal` / `team` / `org` | Who owns the extension |

These appear in `describe()` output and in `runtime.tool_registry` metadata tags.
Enforcement policy (blocking `dev` in production) is the host application's responsibility.

---

## E — Bytecode Impact

None. Manifest is pure Python (Pydantic). BYTECODE_VERSION stays 4. (D1)
