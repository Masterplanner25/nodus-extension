# Changelog

Format: [Keep a Changelog](https://keepachangelog.com)
Versioning: [Semantic Versioning](https://semver.org)

## [Unreleased]

## [0.1.1] — 2026-08-17

### Changed

- **Floated the `nodus-lang` dependency to `>=4.0.0`** (was `>=4.0.0,<5.0.0`).
  The upper bound made this package uninstallable alongside nodus-lang 5.0.0
  (`ResolutionImpossible`), while nothing in the code was incompatible — the
  full suite (126 tests) passes against 5.0.0 unchanged.

  The cap was prophylactic rather than earned; no 5.x break was ever recorded
  here. A hard upper bound on a first-party dependency turns every nodus-lang
  major into a two-repo release train with consumers frozen in between. This
  package's own suite is the check that catches a real break; a cap earns its
  place once a break is known.

## [0.1.0] — 2026-06-10


### Added

**Extension manifest (Phases A–B)**

- `ExtensionManifest` Pydantic model — name, version, description, abi_version,
  min_nodus_version, capabilities, provenance, surfaces
- `ToolSurface` Pydantic model — name (must be dotted), description, schema, version (`v1alpha1`)
- `Provenance` — origin (local/registry/git), trust_class (dev/verified/trusted), owner_class (personal/team/org)
- `load_manifest(path)` — reads and validates `nodus-extension.json`
- 8 `ExtensionError` subclasses: `ManifestError`, `CapabilityError`, `SandboxError`, `AbiError`, `RegistryError`, `InvokeError`, `TimeoutError`

**Capability gates (Phase C)**

- `Capability` enum — 7 capabilities: `filesystem.read`, `filesystem.write`, `network.outbound`, `subprocess.run`, `tool.invoke`, `memory.read`, `memory.write`
- `CapabilityGate` — allowlist enforcement with `require(cap)` and `has(cap)`
- `parse_capabilities(raw)` — validates capability strings at manifest parse time

**Subprocess sandbox runner (Phase D)**

- `SandboxRunner` ABC (v0.2+ will add `DockerRunner`, `VmRunner`)
- `SubprocessRunner` — tier 1 insecure-dev sandbox: spawns `extension.py` as subprocess
- NDJSON IPC protocol over stdin/stdout with per-invoke timeout
- `worker.py` — extension developer API: `register_tool()` + `run_loop()`

**Extension host + registry (Phases E–F)**

- `ExtensionHost` — loads manifest, creates gate and runner, routes invocations
- `ExtensionRegistry` — multi-extension manager: load/unload/list/describe/invoke/lookup

**nodus-lang tool_registry bridge (Phase G)**

- `register_extension_tools(runtime, host)` — registers all `tool/v1alpha1` surfaces in `NodusRuntime.tool_registry` with provenance metadata
- `unregister_extension_tools(runtime, host)` — removes surfaces on unload

**Nodus language bindings (Phase H)**

- `attach_to_runtime(runtime, registry)` — registers 4 host functions: `_ext_load`, `_ext_list`, `_ext_invoke`, `_ext_describe`
- `nd/index.nd` — Nodus wrappers: `ext_load`, `ext_list`, `ext_invoke`, `ext_describe`
- `nodus.nd` entry-point: `nodus-extension = nodus_extension.nd.nd:get_nd_root`

**CLI (Phase I)**

- `python -m nodus_extension` — validate, describe, load, invoke subcommands

**Quality (Phase J)**

- 126 tests, 93% coverage (gate: 75%)
- 8 standing invariants
- End-to-end integration: `hello-ext` fixture (subprocess + Nodus script)
- Install roundtrip verified

### Design Decisions

- **D1** — No new opcodes; BYTECODE_VERSION stays 4
- **D2** — nodus-schema inlined as Pydantic models (not a separate dependency)
- **D3** — Python ≥3.11
- **D4** — Single ABI surface: `tool/v1alpha1`; node/webhook/flow/planner_backend deferred
- **D5** — Manifest format: `nodus-extension.json` (JSON, not YAML)
- **D6** — Subprocess sandbox tier only; OCI container and VM deferred
- **D7** — NDJSON IPC over stdin/stdout
- **D8** — Capability allowlist model; unknown capabilities rejected at parse time
- **D9** — Provenance is informational in v0.1; enforcement is host responsibility
- **D10** — Build backend: hatchling

### Deferred to v0.2+

- OCI container sandbox (Docker), VM strong-sandbox (Firecracker/gVisor)
- `node/v1alpha1`, `webhook/v1alpha1`, `flow/v1alpha1`, `planner_backend/v1alpha1` surfaces
- Trust enforcement (verified/trusted classes require signing/attestation)
- Hot-reload of extensions
- nodus-observability integration
- Extension marketplace/registry discovery
- Pure `.nd` extensions (v0.1 requires Python)
