"""Phase J — standing invariants (8 assertions)."""
from __future__ import annotations

import importlib.metadata
import re
import pytest


class TestBytecodeVersionUnchanged:
    def test_bytecode_version_is_4(self):
        from nodus.compiler.compiler import BYTECODE_VERSION
        assert BYTECODE_VERSION == 4


class TestErrorHierarchy:
    def test_all_eight_errors_are_extension_error_subclasses(self):
        import nodus_extension as e
        for cls in [e.ManifestError, e.CapabilityError, e.SandboxError, e.AbiError,
                    e.RegistryError, e.InvokeError, e.TimeoutError]:
            assert issubclass(cls, e.ExtensionError), f"{cls} not subclass"


class TestCapabilityGateEmpty:
    def test_empty_gate_blocks_all_capabilities(self):
        from nodus_extension.capabilities import CapabilityGate, Capability
        from nodus_extension.errors import CapabilityError
        gate = CapabilityGate(frozenset())
        for cap in Capability:
            with pytest.raises(CapabilityError):
                gate.require(cap)


class TestManifestRejectsUnknownCapability:
    def test_unknown_capability_in_manifest_raises_at_parse_time(self, tmp_path):
        import json
        from nodus_extension.manifest import load_manifest
        from nodus_extension.errors import ManifestError
        (tmp_path / "nodus-extension.json").write_text(json.dumps({
            "name": "x.y", "version": "1.0.0", "description": "d",
            "capabilities": ["totally.unknown"]
        }))
        with pytest.raises(ManifestError):
            load_manifest(str(tmp_path))


class TestToolNameMustBeDotted:
    def test_undotted_tool_name_rejected_in_manifest(self, tmp_path):
        import json
        from nodus_extension.manifest import load_manifest
        from nodus_extension.errors import ManifestError
        (tmp_path / "nodus-extension.json").write_text(json.dumps({
            "name": "x.y", "version": "1.0.0", "description": "d",
            "surfaces": {"tools": [{"name": "nodot", "description": "d"}]}
        }))
        with pytest.raises(ManifestError):
            load_manifest(str(tmp_path))


class TestStoppedRunnerRaisesSandboxError:
    def test_invoke_on_unstarted_runner_raises_sandbox_error(self, tmp_path):
        import json
        from nodus_extension.runner.subprocess import SubprocessRunner
        from nodus_extension.manifest import load_manifest
        from nodus_extension.errors import SandboxError
        (tmp_path / "nodus-extension.json").write_text(json.dumps({
            "name": "x.y", "version": "1.0.0", "description": "d"
        }))
        manifest = load_manifest(str(tmp_path))
        runner = SubprocessRunner(str(tmp_path), manifest)
        with pytest.raises(SandboxError, match="not running"):
            runner.invoke("any.tool", {})


class TestHostFunctionsDontShadowBuiltins:
    def test_ext_prefixed_functions_not_in_builtin_names(self):
        from nodus.builtins.nodus_builtins import BUILTIN_NAMES
        for name in ["_ext_load", "_ext_list", "_ext_invoke", "_ext_describe"]:
            assert name not in BUILTIN_NAMES, f"{name} shadows a builtin"


class TestPackageImportsCleanly:
    def test_import_without_subprocess_or_nodus(self):
        import nodus_extension
        # Compared against the packaging metadata, not a literal: a hardcoded
        # version here goes stale the moment the package is bumped. It did —
        # the 0.1.0 -> 0.1.1 bump for the nodus-lang cap float broke these
        # without anything in the package changing.
        from importlib.metadata import version as _pkg_version

        assert nodus_extension.__version__ == _pkg_version("nodus-extension")

    def test_version_is_semver(self):
        import nodus_extension
        assert re.match(r"^\d+\.\d+\.\d+$", nodus_extension.__version__)

    def test_version_matches_metadata(self):
        import nodus_extension
        meta_version = importlib.metadata.version("nodus-extension")
        assert nodus_extension.__version__ == meta_version
