"""Phase J — pip install roundtrip: package installs cleanly and version matches."""
from __future__ import annotations

import importlib.metadata
import pathlib
import re


class TestInstallRoundtrip:
    def test_package_importable(self):
        import nodus_extension  # noqa: F401

    def test_version_matches_pyproject(self):
        import nodus_extension
        meta_version = importlib.metadata.version("nodus-extension")
        assert nodus_extension.__version__ == meta_version

    def test_version_is_semver(self):
        import nodus_extension
        assert re.match(r"^\d+\.\d+\.\d+$", nodus_extension.__version__)

    def test_nd_entry_point_registered(self):
        eps = importlib.metadata.entry_points(group="nodus.nd")
        names = [ep.name for ep in eps]
        assert "nodus-extension" in names

    def test_nd_root_exists(self):
        from nodus_extension.nd.nd import get_nd_root
        root = pathlib.Path(get_nd_root())
        assert root.is_dir()
        assert (root / "index.nd").exists()

    def test_all_public_exports_importable(self):
        import nodus_extension
        for name in nodus_extension.__all__:
            assert hasattr(nodus_extension, name), f"Missing export: {name}"
