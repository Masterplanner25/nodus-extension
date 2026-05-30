"""Phase G: tool_registry bridge — extension tool surfaces registered in NodusRuntime."""
from __future__ import annotations

import pathlib
import pytest

FIXTURE_DIR = str(pathlib.Path(__file__).parent / "fixtures" / "hello-ext")

nodus = pytest.importorskip("nodus", reason="nodus-lang not on path")


def _runtime():
    from nodus import NodusRuntime
    return NodusRuntime(timeout_ms=None)


class TestBridge:
    def test_register_extension_tools_adds_to_registry(self):
        from nodus_extension.bridge import register_extension_tools
        from nodus_extension.host import ExtensionHost
        runtime = _runtime()
        host = ExtensionHost(FIXTURE_DIR, timeout_s=10.0)
        try:
            host.load()
            register_extension_tools(runtime, host)
            assert runtime.tool_registry.has("test.hello.greet")
        finally:
            host.unload()

    def test_registered_tool_is_invokable(self):
        from nodus_extension.bridge import register_extension_tools
        from nodus_extension.host import ExtensionHost
        runtime = _runtime()
        host = ExtensionHost(FIXTURE_DIR, timeout_s=10.0)
        try:
            host.load()
            register_extension_tools(runtime, host)
            result = runtime.tool_registry.invoke("test.hello.greet", {"name": "Carol"})
            assert result == "Hello, Carol!"
        finally:
            host.unload()

    def test_unregister_removes_tools(self):
        from nodus_extension.bridge import register_extension_tools, unregister_extension_tools
        from nodus_extension.host import ExtensionHost
        runtime = _runtime()
        host = ExtensionHost(FIXTURE_DIR, timeout_s=10.0)
        try:
            host.load()
            register_extension_tools(runtime, host)
            assert runtime.tool_registry.has("test.hello.greet")
            unregister_extension_tools(runtime, host)
            assert not runtime.tool_registry.has("test.hello.greet")
        finally:
            host.unload()

    def test_tool_metadata_includes_extension_info(self):
        from nodus_extension.bridge import register_extension_tools
        from nodus_extension.host import ExtensionHost
        runtime = _runtime()
        host = ExtensionHost(FIXTURE_DIR, timeout_s=10.0)
        try:
            host.load()
            register_extension_tools(runtime, host)
            tool_info = runtime.tool_registry.lookup("test.hello.greet")
            assert tool_info is not None
            meta = tool_info.get("metadata", {})
            assert meta.get("extension_name") == "test.hello"
            assert meta.get("abi_surface") == "tool/v1alpha1"
        finally:
            host.unload()

    def test_tool_listed_in_registry(self):
        from nodus_extension.bridge import register_extension_tools
        from nodus_extension.host import ExtensionHost
        runtime = _runtime()
        host = ExtensionHost(FIXTURE_DIR, timeout_s=10.0)
        try:
            host.load()
            register_extension_tools(runtime, host)
            tools = runtime.tool_registry.list_tools()
            names = [t["name"] for t in tools]
            assert "test.hello.greet" in names
        finally:
            host.unload()
