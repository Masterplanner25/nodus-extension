# nodus-extension Design Doc 02 — Capability Gates

**Doc:** 02-capabilities.md  **Status:** Complete — 2026-05-30
**Decisions grounded:** D8, D9

Capability gates enforce the principle that extensions should declare what they need,
and the host should verify before granting access. In v0.1 this is an allowlist check
before every `host.invoke()` call — the extension must declare `tool.invoke` to call tools.

In v0.2+, the gate will also intercept `std:http`, `std:subprocess`, and memory builtins
inside the sandbox, enforcing the full capability set per sandboxed call.

**CapabilityGate.require(cap):** raises `CapabilityError` immediately if cap not allowed.
Unknown capabilities are rejected at manifest parse time. No deferred enforcement.
