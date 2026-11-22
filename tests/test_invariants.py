"""Phase J — standing invariants (8 assertions)."""
from __future__ import annotations

import importlib.metadata
import re
import pytest


# Run in a fresh interpreter: import every module of `argv[1]` (none if empty),
# then print the opcodes a new nodus VM dispatches.
_OPCODES_AFTER_IMPORT = r"""
import importlib, json, pkgutil, sys
if sys.argv[1]:
    package = importlib.import_module(sys.argv[1])
    for info in pkgutil.walk_packages(package.__path__, sys.argv[1] + "."):
        try:
            importlib.import_module(info.name)
        except ImportError:
            pass  # an optional dependency this environment lacks
from nodus.vm.vm import VM
print(json.dumps(sorted(VM([], {}, code_locs=[], source_path=None)._dispatch)))
"""


def _opcodes_after_importing(package: str) -> list:
    import json
    import os
    import subprocess
    import sys

    env = dict(os.environ, PYTHONPATH=os.pathsep.join(p for p in sys.path if p))
    proc = subprocess.run([sys.executable, "-c", _OPCODES_AFTER_IMPORT, package],
                          capture_output=True, text=True, env=env, timeout=120)
    assert proc.returncode == 0, proc.stderr[-800:]
    return json.loads(proc.stdout.strip().splitlines()[-1])


class TestNoNewOpcodes:
    def test_importing_the_package_leaves_the_opcode_set_alone(self):
        """nodus-extension adds no opcodes.

        This asserted nodus-lang's `BYTECODE_VERSION == 4`. That is nodus-lang's
        number, which this package cannot change, so it guarded nothing here
        and failed when nodus-lang 5.17.0 added opcodes through its own
        extension process (#969). It checks the package instead: importing
        every module of it leaves a nodus VM's opcode set as nodus-lang defines
        it, and the source never reaches for the VM's dispatch table or the
        bytecode version.
        """
        pytest.importorskip("nodus.vm.vm", reason="nodus-lang not importable")
        from pathlib import Path

        bare = _opcodes_after_importing("")
        assert len(bare) > 20, f"read {len(bare)} opcodes: the comparison would prove nothing"
        assert _opcodes_after_importing("nodus_extension") == bare, (
            "importing nodus_extension changed the VM's opcode set")
        vm_internals = re.compile(r"\b(?:vm|VM)\._dispatch\b|_build_dispatch_table|BYTECODE_VERSION\s*=")
        source = Path(__file__).resolve().parents[1] / "src" / "nodus_extension"
        touching = [p.name for p in source.rglob("*.py")
                    if vm_internals.search(p.read_text(encoding="utf-8"))]
        assert not touching, f"{touching} reach into the VM's dispatch table"


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
