# nodus-extension — Design Decision Log (Phase 0)

**Status:** Complete — 2026-05-30
**Decisions:** D1–D10 (all locked)

---

## D1 — No new opcodes

BYTECODE_VERSION stays at 4. nodus-extension adds host functions and .nd wrapper
functions only. No new VM instructions, no compiler changes.

## D2 — nodus-schema is inlined

nodus-schema does not exist as a library (not in any governance doc). Rather than
block on an unbuilt dependency, this library inlines schema validation via Pydantic
models for manifests and ABI surfaces. If nodus-schema is built later, the Pydantic
models are extractable. This is explicitly a "schema-light" v0.1 — the manifest
format is designed to be forward-compatible.

## D3 — Python ≥3.11

Matches nodus-lang 4.0.0 and all other companion libraries.

## D4 — Single ABI surface in v0.1: tool/v1alpha1

Five ABI surfaces were identified in the audit:
- `manifest/v1` — always required (part of the manifest, not a surface)
- `tool/v1alpha1` — registered tools exposed to the host
- `node/v1alpha1` — custom flow nodes (deferred: requires nodus-workflow)
- `webhook/v1alpha1` — outbound webhooks (deferred: requires HTTP server on ext side)
- `flow/v1alpha1` — full flow definitions (deferred: requires DAG compiler integration)
- `planner_backend/v1alpha1` — planner backends (deferred: requires agent framework)

v0.1 ships `tool/v1alpha1` only. The `abi_version` field in the manifest allows future
surfaces to be added without breaking existing extensions.

## D5 — Manifest format: nodus-extension.json

JSON (not YAML) for simplicity and to avoid a YAML parser dependency. File must be
named exactly `nodus-extension.json` and placed in the extension's root directory.

## D6 — Subprocess sandbox tier only in v0.1

Three sandbox tiers from the audit:
1. **insecure-dev subprocess** — plain subprocess (THIS TIER in v0.1)
2. **OCI container** — Docker (deferred to v0.2; requires Docker infra)
3. **strong-sandbox VM** — Firecracker/gVisor (deferred; significant ops complexity)

The `SandboxRunner` ABC allows v0.2 to add `DockerRunner` without API changes.

## D7 — Subprocess IPC: newline-delimited JSON over stdin/stdout

Simple, universal, language-agnostic. Chosen over:
- gRPC: adds heavy dependency for a dev-tier sandbox
- Unix sockets: Windows compatibility concerns
- Pipes with length framing: NDJSON is simpler to debug

Protocol:
- Host → Worker: `{"id": "uuid", "op": "invoke", "name": "tool.name", "args": {...}}\n`
- Worker → Host: `{"id": "uuid", "ok": true, "result": ...}\n`
- Worker → Host: `{"id": "uuid", "ok": false, "error": "message"}\n`
- Host → Worker: `{"op": "shutdown"}\n` (no id; worker exits cleanly)

## D8 — Capability gates: allowlist model

Extensions declare `capabilities` in their manifest. The host creates a `CapabilityGate`
from the declared set. Before any privileged operation, the framework calls
`gate.require(cap)` — raises `CapabilityError` if not in the allowlist.

Unknown capability strings (not in the `Capability` enum) are rejected at manifest
parse time (`ManifestError`), not at invocation time.

## D9 — Provenance: informational in v0.1

Three provenance axes:
- `origin`: `local` | `registry` | `git` — where the extension came from
- `trust_class`: `dev` | `verified` | `trusted` — operator-assigned trust tier
- `owner_class`: `personal` | `team` | `org` — who owns the extension

All three are stored in the manifest and exposed in `describe()`. Enforcement
(e.g., blocking `dev` extensions in production) is the host application's
responsibility — the framework provides the data, not the policy.

## D10 — Build backend: hatchling

Consistent with nodus-a2a and nodus-memory.
