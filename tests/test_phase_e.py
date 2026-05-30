"""Phase E: ExtensionHost — manifest validation + runner wiring."""
from __future__ import annotations

import json
import pathlib
import pytest

FIXTURE_DIR = str(pathlib.Path(__file__).parent / "fixtures" / "hello-ext")


class TestExtensionHost:
    def _host(self) -> "ExtensionHost":
        from nodus_extension.host import ExtensionHost
        return ExtensionHost(FIXTURE_DIR, timeout_s=10.0)

    def test_load_returns_manifest(self):
        host = self._host()
        try:
            m = host.load()
            assert m.name == "test.hello"
        finally:
            host.unload()

    def test_is_loaded_after_load(self):
        host = self._host()
        assert not host.is_loaded
        try:
            host.load()
            assert host.is_loaded
        finally:
            host.unload()

    def test_is_not_loaded_after_unload(self):
        host = self._host()
        host.load()
        host.unload()
        assert not host.is_loaded

    def test_double_load_raises_registry_error(self):
        from nodus_extension.errors import RegistryError
        host = self._host()
        try:
            host.load()
            with pytest.raises(RegistryError, match="already loaded"):
                host.load()
        finally:
            host.unload()

    def test_invoke_returns_result(self):
        host = self._host()
        try:
            host.load()
            result = host.invoke("test.hello.greet", {"name": "Eve"})
            assert result == "Hello, Eve!"
        finally:
            host.unload()

    def test_invoke_before_load_raises_sandbox_error(self):
        from nodus_extension.errors import SandboxError
        host = self._host()
        with pytest.raises(SandboxError, match="not loaded"):
            host.invoke("test.hello.greet", {"name": "X"})

    def test_invoke_blocked_without_capability(self, tmp_path):
        from nodus_extension.host import ExtensionHost
        from nodus_extension.errors import CapabilityError
        import sys
        src_root = str(pathlib.Path(__file__).parent.parent / "src")
        manifest_data = {
            "name": "test.nocap", "version": "1.0.0", "description": "no caps",
            "capabilities": [],
            "surfaces": {"tools": [{"name": "test.nocap.hello", "description": "hello"}]}
        }
        (tmp_path / "nodus-extension.json").write_text(json.dumps(manifest_data))
        (tmp_path / "extension.py").write_text(
            f'import sys\nsys.path.insert(0, {src_root!r})\n'
            f'from nodus_extension.worker import register_tool, run_loop\n'
            f'register_tool("test.nocap.hello", lambda args: "hi")\n'
            f'run_loop()\n'
        )
        host = ExtensionHost(str(tmp_path), timeout_s=5.0)
        try:
            host.load()
            with pytest.raises(CapabilityError):
                host.invoke("test.nocap.hello", {})
        finally:
            host.unload()

    def test_describe_returns_expected_shape(self):
        host = self._host()
        try:
            host.load()
            d = host.describe()
            assert d["name"] == "test.hello"
            assert d["loaded"] is True
            assert isinstance(d["tools"], list)
            assert d["tools"][0]["name"] == "test.hello.greet"
        finally:
            host.unload()

    def test_describe_before_load_returns_empty(self):
        host = self._host()
        d = host.describe()
        assert d == {}

    def test_name_property(self):
        host = self._host()
        assert host.name is None
        try:
            host.load()
            assert host.name == "test.hello"
        finally:
            host.unload()

    def test_unload_twice_is_safe(self):
        host = self._host()
        host.load()
        host.unload()
        host.unload()  # no exception
