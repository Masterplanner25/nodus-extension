"""Phase C: CapabilityGate — allowlist enforcement."""
from __future__ import annotations

import pytest
from nodus_extension.capabilities import Capability, CapabilityGate, parse_capabilities
from nodus_extension.errors import CapabilityError


class TestParseCapabilities:
    def test_empty_list_returns_empty(self):
        assert parse_capabilities([]) == frozenset()

    def test_single_known_cap(self):
        result = parse_capabilities(["filesystem.read"])
        assert Capability.filesystem_read in result

    def test_all_known_caps(self):
        all_caps = [e.value for e in Capability]
        result = parse_capabilities(all_caps)
        assert len(result) == len(all_caps)

    def test_unknown_cap_raises(self):
        with pytest.raises(ValueError, match="unknown capability"):
            parse_capabilities(["totally.fake"])

    def test_returns_frozenset(self):
        result = parse_capabilities(["tool.invoke"])
        assert isinstance(result, frozenset)

    def test_deduplication(self):
        result = parse_capabilities(["tool.invoke", "tool.invoke"])
        assert len(result) == 1


class TestCapabilityGate:
    def _gate(self, *caps: str) -> CapabilityGate:
        return CapabilityGate.from_manifest_strings(list(caps))

    def test_allowed_cap_passes(self):
        gate = self._gate("filesystem.read")
        gate.require(Capability.filesystem_read)  # no exception

    def test_disallowed_cap_raises(self):
        gate = self._gate("filesystem.read")
        with pytest.raises(CapabilityError):
            gate.require(Capability.filesystem_write)

    def test_empty_allowlist_blocks_all(self):
        gate = self._gate()
        for cap in Capability:
            with pytest.raises(CapabilityError):
                gate.require(cap)

    def test_has_returns_true_for_allowed(self):
        gate = self._gate("tool.invoke")
        assert gate.has(Capability.tool_invoke)

    def test_has_returns_false_for_disallowed(self):
        gate = self._gate("tool.invoke")
        assert not gate.has(Capability.memory_read)

    def test_error_includes_extension_name(self):
        gate = CapabilityGate(frozenset(), extension_name="myapp.ext")
        with pytest.raises(CapabilityError) as exc_info:
            gate.require(Capability.network_outbound)
        assert "myapp.ext" in str(exc_info.value)

    def test_allowed_property(self):
        gate = self._gate("memory.read", "memory.write")
        assert Capability.memory_read in gate.allowed
        assert Capability.memory_write in gate.allowed
        assert Capability.tool_invoke not in gate.allowed

    def test_from_manifest_strings(self):
        gate = CapabilityGate.from_manifest_strings(
            ["filesystem.read", "network.outbound"], extension_name="test.ext"
        )
        assert gate.has(Capability.filesystem_read)
        assert gate.has(Capability.network_outbound)
        assert not gate.has(Capability.filesystem_write)


class TestCapabilityEnum:
    def test_seven_capabilities(self):
        assert len(list(Capability)) == 7

    def test_all_capability_values_dotted(self):
        for cap in Capability:
            assert "." in cap.value, f"{cap.name} has no dot in value {cap.value!r}"

    def test_capability_is_string_enum(self):
        assert isinstance(Capability.tool_invoke, str)
        assert Capability.tool_invoke == "tool.invoke"
