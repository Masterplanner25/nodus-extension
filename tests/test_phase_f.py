"""Phase F: ExtensionRegistry — load/unload/list/describe."""
from __future__ import annotations

import json
import pathlib
import pytest

FIXTURE_DIR = str(pathlib.Path(__file__).parent / "fixtures" / "hello-ext")


def _registry():
    from nodus_extension.registry import ExtensionRegistry
    return ExtensionRegistry()


class TestExtensionRegistry:
    def test_load_returns_manifest(self):
        r = _registry()
        try:
            m = r.load(FIXTURE_DIR)
            assert m.name == "test.hello"
        finally:
            r.unload("test.hello")

    def test_contains_after_load(self):
        r = _registry()
        try:
            r.load(FIXTURE_DIR)
            assert "test.hello" in r
        finally:
            r.unload("test.hello")

    def test_not_contains_before_load(self):
        r = _registry()
        assert "test.hello" not in r

    def test_unload_removes(self):
        r = _registry()
        r.load(FIXTURE_DIR)
        r.unload("test.hello")
        assert "test.hello" not in r

    def test_unload_nonexistent_raises(self):
        from nodus_extension.errors import RegistryError
        r = _registry()
        with pytest.raises(RegistryError, match="not loaded"):
            r.unload("test.nonexistent")

    def test_duplicate_load_raises(self):
        from nodus_extension.errors import RegistryError
        r = _registry()
        try:
            r.load(FIXTURE_DIR)
            with pytest.raises(RegistryError, match="already loaded"):
                r.load(FIXTURE_DIR)
        finally:
            r.unload("test.hello")

    def test_list_returns_all(self, tmp_path):
        import sys
        src_root = str(pathlib.Path(__file__).parent.parent / "src")
        ext_data = {
            "name": "test.second", "version": "1.0.0", "description": "second",
            "capabilities": ["tool.invoke"],
            "surfaces": {"tools": [{"name": "test.second.foo", "description": "foo"}]}
        }
        (tmp_path / "nodus-extension.json").write_text(json.dumps(ext_data))
        (tmp_path / "extension.py").write_text(
            f'import sys\nsys.path.insert(0, {src_root!r})\n'
            f'from nodus_extension.worker import register_tool, run_loop\n'
            f'register_tool("test.second.foo", lambda args: "bar")\n'
            f'run_loop()\n'
        )
        r = _registry()
        try:
            r.load(FIXTURE_DIR)
            r.load(str(tmp_path))
            items = r.list()
            names = {d["name"] for d in items}
            assert "test.hello" in names
            assert "test.second" in names
        finally:
            r.unload("test.hello")
            r.unload("test.second")

    def test_describe_returns_dict(self):
        r = _registry()
        try:
            r.load(FIXTURE_DIR)
            d = r.describe("test.hello")
            assert d is not None
            assert d["name"] == "test.hello"
        finally:
            r.unload("test.hello")

    def test_describe_missing_returns_none(self):
        r = _registry()
        assert r.describe("nonexistent") is None

    def test_invoke_returns_result(self):
        r = _registry()
        try:
            r.load(FIXTURE_DIR)
            result = r.invoke("test.hello", "test.hello.greet", {"name": "Bob"})
            assert result == "Hello, Bob!"
        finally:
            r.unload("test.hello")

    def test_invoke_missing_extension_raises(self):
        from nodus_extension.errors import RegistryError
        r = _registry()
        with pytest.raises(RegistryError, match="not loaded"):
            r.invoke("test.nonexistent", "test.nonexistent.foo", {})

    def test_len(self):
        r = _registry()
        assert len(r) == 0
        try:
            r.load(FIXTURE_DIR)
            assert len(r) == 1
        finally:
            r.unload("test.hello")
        assert len(r) == 0

    def test_lookup_returns_host(self):
        from nodus_extension.host import ExtensionHost
        r = _registry()
        try:
            r.load(FIXTURE_DIR)
            host = r.lookup("test.hello")
            assert isinstance(host, ExtensionHost)
        finally:
            r.unload("test.hello")

    def test_lookup_missing_returns_none(self):
        r = _registry()
        assert r.lookup("missing") is None
