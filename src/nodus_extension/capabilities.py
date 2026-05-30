from __future__ import annotations

from enum import Enum

from nodus_extension.errors import CapabilityError


class Capability(str, Enum):
    filesystem_read = "filesystem.read"
    filesystem_write = "filesystem.write"
    network_outbound = "network.outbound"
    subprocess_run = "subprocess.run"
    tool_invoke = "tool.invoke"
    memory_read = "memory.read"
    memory_write = "memory.write"

    @classmethod
    def _all_values(cls) -> set[str]:
        return {e.value for e in cls}


def parse_capabilities(raw: list[str]) -> frozenset[Capability]:
    """Parse a list of capability strings from a manifest.

    Raises ValueError if any string is not a recognized Capability.
    """
    result = set()
    known = Capability._all_values()
    for cap_str in raw:
        if cap_str not in known:
            raise ValueError(
                f"unknown capability: {cap_str!r}; "
                f"supported: {sorted(known)}"
            )
        result.add(Capability(cap_str))
    return frozenset(result)


class CapabilityGate:
    """Enforces the allowlist of capabilities for one extension instance."""

    def __init__(self, allowed: frozenset[Capability], extension_name: str | None = None) -> None:
        self._allowed = allowed
        self._extension_name = extension_name

    @property
    def allowed(self) -> frozenset[Capability]:
        return self._allowed

    def require(self, cap: Capability) -> None:
        """Raise CapabilityError if *cap* is not in the allowlist."""
        if cap not in self._allowed:
            raise CapabilityError(cap.value, extension=self._extension_name)

    def has(self, cap: Capability) -> bool:
        return cap in self._allowed

    @classmethod
    def from_manifest_strings(
        cls, raw: list[str], extension_name: str | None = None
    ) -> "CapabilityGate":
        return cls(parse_capabilities(raw), extension_name=extension_name)
