# nodus-extension Design Doc 04 — Extension Registry

**Doc:** 04-registry.md  **Status:** Complete — 2026-05-30

`ExtensionRegistry` maps extension names to `ExtensionHost` instances. Load is by directory
path; the registry reads the manifest to get the name, then indexes by name.

Duplicate names raise `RegistryError` immediately (before the host subprocess starts). The
host subprocess is started eagerly in `load()` so it's ready to handle invoke calls without
latency on first use.

`unload()` calls `host.unload()` which stops the subprocess cleanly.
`list()` returns `describe()` for all loaded extensions.
`lookup(name)` returns the `ExtensionHost` directly for callers that need low-level access.
