"""Phase H: Nodus language bindings — import nodus-extension, ext_load/invoke."""
from __future__ import annotations

import pathlib
import pytest

FIXTURE_DIR = str(pathlib.Path(__file__).parent / "fixtures" / "hello-ext")

nodus = pytest.importorskip("nodus", reason="nodus-lang not on path")


def _runtime_with_registry():
    from nodus import NodusRuntime
    from nodus_extension.registry import ExtensionRegistry
    from nodus_extension.nodus_bindings import attach_to_runtime
    registry = ExtensionRegistry()
    runtime = NodusRuntime(timeout_ms=None)
    attach_to_runtime(runtime, registry)
    return runtime, registry


class TestNodusBindings:
    def test_attach_registers_four_functions(self):
        from nodus import NodusRuntime
        from nodus_extension.registry import ExtensionRegistry
        from nodus_extension.nodus_bindings import attach_to_runtime
        registry = ExtensionRegistry()
        runtime = NodusRuntime(timeout_ms=None)
        attach_to_runtime(runtime, registry)
        for name in ["_ext_load", "_ext_list", "_ext_invoke", "_ext_describe"]:
            assert name in runtime._host_functions, f"{name} not registered"

    def test_import_nodus_extension_succeeds(self):
        runtime, _ = _runtime_with_registry()
        result = runtime.run_source('import "nodus-extension"\nprint("loaded")')
        assert result["ok"], result["errors"]
        assert "loaded" in result["stdout"]

    def test_ext_load_via_language(self):
        runtime, registry = _runtime_with_registry()
        try:
            result = runtime.run_source(f'''
import "nodus-extension"
let name = ext_load("{FIXTURE_DIR.replace(chr(92), '/')}")
print(name)
''')
            assert result["ok"], result["errors"]
            assert "test.hello" in result["stdout"]
        finally:
            if "test.hello" in registry:
                registry.unload("test.hello")

    def test_ext_invoke_via_language(self):
        runtime, registry = _runtime_with_registry()
        try:
            fixture_path = FIXTURE_DIR.replace("\\", "/")
            # Pass empty args — hello-ext uses "World" as default
            result = runtime.run_source(f'''
import "nodus-extension"
ext_load("{fixture_path}")
let r = ext_invoke("test.hello", "test.hello.greet", "{{}}")
print(r)
''')
            assert result["ok"], result["errors"]
            assert "Hello" in result["stdout"]
        finally:
            if "test.hello" in registry:
                registry.unload("test.hello")

    def test_ext_list_via_language(self):
        runtime, registry = _runtime_with_registry()
        try:
            fixture_path = FIXTURE_DIR.replace("\\", "/")
            result = runtime.run_source(f'''
import "nodus-extension"
ext_load("{fixture_path}")
let items = ext_list()
print(items)
''')
            assert result["ok"], result["errors"]
            assert "test.hello" in result["stdout"]
        finally:
            if "test.hello" in registry:
                registry.unload("test.hello")

    def test_ext_describe_via_language(self):
        runtime, registry = _runtime_with_registry()
        try:
            fixture_path = FIXTURE_DIR.replace("\\", "/")
            result = runtime.run_source(f'''
import "nodus-extension"
ext_load("{fixture_path}")
let d = ext_describe("test.hello")
print(d)
''')
            assert result["ok"], result["errors"]
            assert "test.hello" in result["stdout"]
        finally:
            if "test.hello" in registry:
                registry.unload("test.hello")

    def test_version_accessible_after_import(self):
        runtime, _ = _runtime_with_registry()
        result = runtime.run_source('import "nodus-extension"\nprint(_version)')
        assert result["ok"], result["errors"]
        assert "0.1.0" in result["stdout"]
