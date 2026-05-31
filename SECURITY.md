# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x | Yes |

## Sandbox tier warning

v0.1 uses **subprocess sandbox only** (insecure-dev tier). This means extensions
run as a child process of the host with the same OS user permissions. Do not
load untrusted extensions in production until OCI/VM sandboxing (v0.2+) is available.

The capability gate (`CapabilityGate`) enforces declared capabilities within the
Nodus protocol, but does not prevent a malicious `extension.py` from escaping the
subprocess. Use `TrustClass.DEV` for local development extensions only.

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Report privately to: **shawnknight@the-master-plan.com**

Include a description, steps to reproduce, and potential impact.
You will receive a response within 72 hours.
