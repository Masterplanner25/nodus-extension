"""Phase B: manifest parsing, Pydantic validation, provenance."""
from __future__ import annotations

import json
import pathlib
import tempfile
import pytest

FIXTURE_DIR = pathlib.Path(__file__).parent / "fixtures" / "hello-ext"


def _write_manifest(tmp_path: pathlib.Path, data: dict) -> str:
    (tmp_path / "nodus-extension.json").write_text(json.dumps(data))
    return str(tmp_path)


class TestLoadManifest:
    def test_load_valid_fixture(self):
        from nodus_extension.manifest import load_manifest
        m = load_manifest(str(FIXTURE_DIR))
        assert m.name == "test.hello"
        assert m.version == "1.0.0"
        assert len(m.surfaces.tools) == 1
        assert m.surfaces.tools[0].name == "test.hello.greet"

    def test_missing_file_raises_manifest_error(self, tmp_path):
        from nodus_extension.manifest import load_manifest
        from nodus_extension import ManifestError
        with pytest.raises(ManifestError, match="not found"):
            load_manifest(str(tmp_path))

    def test_invalid_json_raises_manifest_error(self, tmp_path):
        from nodus_extension.manifest import load_manifest
        from nodus_extension import ManifestError
        (tmp_path / "nodus-extension.json").write_text("{not valid json}")
        with pytest.raises(ManifestError, match="invalid JSON"):
            load_manifest(str(tmp_path))

    def test_missing_required_field_raises_manifest_error(self, tmp_path):
        from nodus_extension.manifest import load_manifest
        from nodus_extension import ManifestError
        _write_manifest(tmp_path, {"version": "1.0.0"})  # missing name
        with pytest.raises(ManifestError):
            load_manifest(str(tmp_path))

    def test_unsupported_abi_version_raises_abi_error(self, tmp_path):
        from nodus_extension.manifest import load_manifest
        from nodus_extension import AbiError
        _write_manifest(tmp_path, {
            "name": "x.y", "version": "1.0.0", "description": "d", "abi_version": "99"
        })
        with pytest.raises(AbiError):
            load_manifest(str(tmp_path))

    def test_unknown_capability_raises_manifest_error(self, tmp_path):
        from nodus_extension.manifest import load_manifest
        from nodus_extension import ManifestError
        _write_manifest(tmp_path, {
            "name": "x.y", "version": "1.0.0", "description": "d",
            "capabilities": ["totally.fake"]
        })
        with pytest.raises(ManifestError):
            load_manifest(str(tmp_path))

    def test_as_dict_round_trips(self):
        from nodus_extension.manifest import load_manifest
        m = load_manifest(str(FIXTURE_DIR))
        d = m.as_dict()
        assert d["name"] == "test.hello"
        assert len(d["surfaces"]["tools"]) == 1
        assert d["surfaces"]["tools"][0]["name"] == "test.hello.greet"


class TestToolSurface:
    def test_valid_tool_surface(self):
        from nodus_extension.manifest import ToolSurface
        ts = ToolSurface(name="myapp.tool", description="does something")
        assert ts.name == "myapp.tool"
        assert ts.version == "v1alpha1"

    def test_undotted_name_rejected(self):
        from nodus_extension.manifest import ToolSurface
        from pydantic import ValidationError
        with pytest.raises(ValidationError, match="dotted"):
            ToolSurface(name="nodot", description="d")

    def test_empty_description_rejected(self):
        from nodus_extension.manifest import ToolSurface
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ToolSurface(name="myapp.tool", description="   ")

    def test_unsupported_surface_version_rejected(self):
        from nodus_extension.manifest import ToolSurface
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ToolSurface(name="myapp.tool", description="d", version="v99")

    def test_schema_field_optional(self):
        from nodus_extension.manifest import ToolSurface
        ts = ToolSurface(name="myapp.tool", description="d")
        assert ts.schema_ == {}

    def test_schema_preserved(self):
        from nodus_extension.manifest import ToolSurface
        schema = {"type": "object", "properties": {"x": {"type": "string"}}}
        ts = ToolSurface(name="myapp.tool", description="d", schema=schema)
        assert ts.schema_ == schema


class TestProvenance:
    def test_defaults(self):
        from nodus_extension.provenance import Provenance, Origin, TrustClass, OwnerClass
        p = Provenance()
        assert p.origin == Origin.local
        assert p.trust_class == TrustClass.dev
        assert p.owner_class == OwnerClass.personal

    def test_custom_values(self):
        from nodus_extension.provenance import Provenance, Origin, TrustClass, OwnerClass
        p = Provenance(origin="git", trust_class="verified", owner_class="org")
        assert p.origin == Origin.git
        assert p.trust_class == TrustClass.verified
        assert p.owner_class == OwnerClass.org

    def test_invalid_origin_raises(self):
        from nodus_extension.provenance import Provenance
        with pytest.raises(ValueError):
            Provenance(origin="unknown")

    def test_as_dict(self):
        from nodus_extension.provenance import Provenance
        d = Provenance().as_dict()
        assert d == {"origin": "local", "trust_class": "dev", "owner_class": "personal"}

    def test_manifest_provenance_converts(self):
        from nodus_extension.manifest import load_manifest
        m = load_manifest(str(FIXTURE_DIR))
        p = m.get_provenance()
        assert p.origin.value == "local"
        assert p.trust_class.value == "dev"


class TestExtensionManifest:
    def test_no_capabilities_allowed(self, tmp_path):
        from nodus_extension.manifest import load_manifest
        _write_manifest(tmp_path, {
            "name": "myapp.ext", "version": "1.0.0", "description": "test",
            "capabilities": []
        })
        m = load_manifest(str(tmp_path))
        assert m.capabilities == []

    def test_all_capabilities_accepted(self, tmp_path):
        from nodus_extension.manifest import load_manifest
        caps = [
            "filesystem.read", "filesystem.write", "network.outbound",
            "subprocess.run", "tool.invoke", "memory.read", "memory.write"
        ]
        _write_manifest(tmp_path, {
            "name": "myapp.ext", "version": "1.0.0", "description": "test",
            "capabilities": caps
        })
        m = load_manifest(str(tmp_path))
        assert set(m.capabilities) == set(caps)

    def test_default_provenance_when_omitted(self, tmp_path):
        from nodus_extension.manifest import load_manifest
        _write_manifest(tmp_path, {
            "name": "myapp.ext", "version": "1.0.0", "description": "test"
        })
        m = load_manifest(str(tmp_path))
        assert m.provenance.origin == "local"
