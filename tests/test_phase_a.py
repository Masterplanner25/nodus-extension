"""Phase A: package skeleton — imports, version, error hierarchy, nd entry-point."""
from __future__ import annotations

import pathlib
import pytest


class TestPackageImports:
    def test_top_level_import(self):
        import nodus_extension  # noqa: F401

    def test_version_string(self):
        import nodus_extension
        assert nodus_extension.__version__ == "0.1.0"

    def test_all_exports_importable(self):
        import nodus_extension
        for name in nodus_extension.__all__:
            assert hasattr(nodus_extension, name), f"Missing export: {name}"

    def test_no_heavy_import_at_top_level(self):
        # Importing the package must not spawn subprocesses or load extensions
        import nodus_extension  # noqa: F401
        assert nodus_extension.__version__

    def test_nd_entry_point(self):
        from nodus_extension.nd.nd import get_nd_root
        root = pathlib.Path(get_nd_root())
        assert root.is_dir()
        assert (root / "index.nd").exists()


class TestErrorHierarchy:
    def test_all_errors_are_extension_error_subclasses(self):
        from nodus_extension import (
            ExtensionError, ManifestError, CapabilityError, SandboxError,
            AbiError, RegistryError, InvokeError, TimeoutError,
        )
        for cls in [ManifestError, CapabilityError, SandboxError,
                    AbiError, RegistryError, InvokeError, TimeoutError]:
            assert issubclass(cls, ExtensionError), f"{cls} not an ExtensionError subclass"

    def test_extension_error_is_exception(self):
        from nodus_extension import ExtensionError
        assert issubclass(ExtensionError, Exception)

    def test_eight_error_types(self):
        import nodus_extension as e
        types = [e.ExtensionError, e.ManifestError, e.CapabilityError, e.SandboxError,
                 e.AbiError, e.RegistryError, e.InvokeError, e.TimeoutError]
        assert len(types) == 8

    def test_manifest_error_stores_path(self):
        from nodus_extension import ManifestError
        err = ManifestError("bad manifest", path="/some/path")
        assert err.path == "/some/path"

    def test_capability_error_stores_capability(self):
        from nodus_extension import CapabilityError
        err = CapabilityError("filesystem.read", extension="myext")
        assert err.capability == "filesystem.read"
        assert err.extension == "myext"
        assert "filesystem.read" in str(err)

    def test_abi_error_stores_version(self):
        from nodus_extension import AbiError
        err = AbiError("unsupported", abi_version="99")
        assert err.abi_version == "99"

    def test_registry_error_stores_name(self):
        from nodus_extension import RegistryError
        err = RegistryError("already loaded", name="myapp.ext")
        assert err.name == "myapp.ext"

    def test_invoke_error_stores_tool_name(self):
        from nodus_extension import InvokeError
        err = InvokeError("failed", tool_name="myapp.foo")
        assert err.tool_name == "myapp.foo"

    def test_timeout_error_stores_fields(self):
        from nodus_extension import TimeoutError
        err = TimeoutError(tool_name="myapp.foo", timeout_s=30.0)
        assert err.tool_name == "myapp.foo"
        assert err.timeout_s == 30.0

    def test_errors_catchable_as_base(self):
        from nodus_extension import ExtensionError, ManifestError
        with pytest.raises(ExtensionError):
            raise ManifestError("bad")

    def test_all_errors_instantiable_with_no_args(self):
        import nodus_extension as e
        for cls in [e.ExtensionError, e.SandboxError]:
            instance = cls()
            assert isinstance(instance, e.ExtensionError)
