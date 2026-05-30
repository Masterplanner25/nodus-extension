# nodus-extension Design Doc 06 — Deferred Features (v0.2+)

**Doc:** 06-deferred.md  **Status:** Complete — 2026-05-30

## DD-1 — OCI container sandbox (Docker)

`DockerRunner` implementing `SandboxRunner`. Requires Docker installed. Resource limits
(CPU, memory, network) via Docker cgroup constraints. Extension image must include
`nodus_extension.worker` in its Python environment.

## DD-2 — VM strong-sandbox (Firecracker / gVisor)

For production deployments with untrusted third-party extensions. Significant ops complexity;
deferred until there is a clear demand signal.

## DD-3 — Additional ABI surfaces

`node/v1alpha1` requires nodus-workflow to be built. `webhook/v1alpha1` requires the
extension to run an HTTP server (complicates the subprocess model). `flow/v1alpha1` and
`planner_backend/v1alpha1` require the agent framework.

## DD-4 — Trust enforcement

The `verified` and `trusted` trust classes require code signing or an attestation server.
v0.1 stores trust_class as metadata but does not enforce policy. v0.2 will add
`CapabilityPolicy` that blocks extensions below a configured trust tier.

## DD-5 — Hot-reload

File watcher that detects changes to `nodus-extension.json` or `extension.py`, stops the
old subprocess, and starts a fresh one — without tearing down the `ExtensionHost`.

## DD-6 — Pure .nd extensions

Extensions whose tools are implemented in Nodus scripts rather than Python. Requires a
Nodus execution host on the worker side and mapping from the NDJSON protocol to `run_source()`.

## DD-7 — nodus-observability integration

OTel spans on every `invoke()` call and subprocess lifecycle event. Blocked on
`nodus-observe` being built (v5.0 roadmap).

## DD-8 — Extension marketplace / registry discovery

Discovery of extensions by name/capability from a central registry. Requires external
registry service.
