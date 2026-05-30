"""Phase J — end-to-end integration tests."""
from __future__ import annotations

import pathlib
import pytest

FIXTURE_DIR = str(pathlib.Path(__file__).parent / "fixtures" / "hello-ext")

nodus = pytest.importorskip("nodus", reason="nodus-lang not on path")


class TestFullWorkflow:
    def test_load_and_invoke_via_nodus_script(self):
        from nodus import NodusRuntime
        from nodus_extension import ExtensionRegistry, attach_to_runtime

        registry = ExtensionRegistry()
        registry.load(FIXTURE_DIR)
        runtime = NodusRuntime(timeout_ms=None)
        attach_to_runtime(runtime, registry)

        try:
            fixture_path = FIXTURE_DIR.replace("\\", "/")
            result = runtime.run_source(f'''
import "nodus-extension"
let r = ext_invoke("test.hello", "test.hello.greet", "{{}}")
print(r)
''')
            assert result["ok"], result["errors"]
            assert "Hello" in result["stdout"]
        finally:
            registry.unload("test.hello")

    def test_multiple_invocations_same_extension(self):
        from nodus_extension import ExtensionRegistry

        registry = ExtensionRegistry()
        registry.load(FIXTURE_DIR)
        try:
            for name in ["Alice", "Bob", "Carol"]:
                result = registry.invoke("test.hello", "test.hello.greet", {"name": name})
                assert result == f"Hello, {name}!"
        finally:
            registry.unload("test.hello")

    def test_tool_bridge_and_nodus_invocation(self):
        from nodus import NodusRuntime
        from nodus_extension import ExtensionRegistry
        from nodus_extension.bridge import register_extension_tools
        from nodus_extension.host import ExtensionHost

        runtime = NodusRuntime(timeout_ms=None)
        host = ExtensionHost(FIXTURE_DIR, timeout_s=10.0)
        try:
            host.load()
            register_extension_tools(runtime, host)
            result = runtime.tool_registry.invoke("test.hello.greet", {"name": "Dave"})
            assert result == "Hello, Dave!"
        finally:
            host.unload()

    def test_capability_enforcement_in_full_flow(self, tmp_path):
        import json
        import sys
        from nodus_extension import ExtensionRegistry, CapabilityError

        src_root = str(pathlib.Path(__file__).parent.parent / "src")
        manifest_data = {
            "name": "test.nocap2", "version": "1.0.0", "description": "no caps",
            "capabilities": [],
            "surfaces": {"tools": [{"name": "test.nocap2.op", "description": "op"}]}
        }
        (tmp_path / "nodus-extension.json").write_text(json.dumps(manifest_data))
        (tmp_path / "extension.py").write_text(
            f'import sys\nsys.path.insert(0, {src_root!r})\n'
            f'from nodus_extension.worker import register_tool, run_loop\n'
            f'register_tool("test.nocap2.op", lambda args: "ok")\n'
            f'run_loop()\n'
        )
        registry = ExtensionRegistry()
        registry.load(str(tmp_path))
        try:
            with pytest.raises(CapabilityError):
                registry.invoke("test.nocap2", "test.nocap2.op", {})
        finally:
            registry.unload("test.nocap2")

    def test_unload_stops_subprocess(self):
        from nodus_extension import ExtensionRegistry

        registry = ExtensionRegistry()
        registry.load(FIXTURE_DIR)
        host = registry.lookup("test.hello")
        assert host.is_loaded
        registry.unload("test.hello")
        assert not host.is_loaded
