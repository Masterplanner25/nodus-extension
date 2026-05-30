from __future__ import annotations

import json
import pathlib
import re
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from nodus_extension.errors import AbiError, ManifestError
from nodus_extension.provenance import Origin, OwnerClass, Provenance, TrustClass

_SUPPORTED_ABI_VERSIONS = {"1"}
_DOTTED_RE = re.compile(r"^[a-z0-9_]+(\.[a-z0-9_]+)+$")


class ProvenanceModel(BaseModel):
    origin: str = "local"
    trust_class: str = "dev"
    owner_class: str = "personal"

    @field_validator("origin")
    @classmethod
    def _check_origin(cls, v: str) -> str:
        try:
            Origin(v)
        except ValueError:
            raise ValueError(f"unknown origin: {v!r}; must be one of {[e.value for e in Origin]}")
        return v

    @field_validator("trust_class")
    @classmethod
    def _check_trust(cls, v: str) -> str:
        try:
            TrustClass(v)
        except ValueError:
            raise ValueError(f"unknown trust_class: {v!r}; must be one of {[e.value for e in TrustClass]}")
        return v

    @field_validator("owner_class")
    @classmethod
    def _check_owner(cls, v: str) -> str:
        try:
            OwnerClass(v)
        except ValueError:
            raise ValueError(f"unknown owner_class: {v!r}; must be one of {[e.value for e in OwnerClass]}")
        return v

    def to_provenance(self) -> Provenance:
        return Provenance(
            origin=Origin(self.origin),
            trust_class=TrustClass(self.trust_class),
            owner_class=OwnerClass(self.owner_class),
        )


class ToolSurface(BaseModel):
    name: str
    description: str
    schema_: dict[str, Any] = Field(default_factory=dict, alias="schema")
    version: str = "v1alpha1"

    model_config = {"populate_by_name": True}

    @field_validator("name")
    @classmethod
    def _check_name(cls, v: str) -> str:
        if not _DOTTED_RE.match(v):
            raise ValueError(
                f"tool surface name must use dotted namespacing (e.g. 'myapp.tool'): {v!r}"
            )
        return v

    @field_validator("version")
    @classmethod
    def _check_version(cls, v: str) -> str:
        if v != "v1alpha1":
            raise ValueError(f"only 'v1alpha1' is supported for tool surfaces: {v!r}")
        return v

    @field_validator("description")
    @classmethod
    def _check_description(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("tool surface description must not be empty")
        return v

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "schema": self.schema_,
            "version": self.version,
        }


class ExtensionSurfaces(BaseModel):
    tools: list[ToolSurface] = Field(default_factory=list)


class ExtensionManifest(BaseModel):
    name: str
    version: str
    description: str
    abi_version: str = "1"
    min_nodus_version: str = "4.0.0"
    capabilities: list[str] = Field(default_factory=list)
    provenance: ProvenanceModel = Field(default_factory=ProvenanceModel)
    surfaces: ExtensionSurfaces = Field(default_factory=ExtensionSurfaces)

    @field_validator("name")
    @classmethod
    def _check_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("extension name must not be empty")
        return v

    @field_validator("description")
    @classmethod
    def _check_description(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("extension description must not be empty")
        return v

    @field_validator("abi_version")
    @classmethod
    def _check_abi(cls, v: str) -> str:
        if v not in _SUPPORTED_ABI_VERSIONS:
            raise ValueError(
                f"unsupported abi_version: {v!r}; supported: {sorted(_SUPPORTED_ABI_VERSIONS)}"
            )
        return v

    @model_validator(mode="after")
    def _validate_capabilities(self) -> "ExtensionManifest":
        from nodus_extension.capabilities import parse_capabilities
        try:
            parse_capabilities(self.capabilities)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        return self

    def get_provenance(self) -> Provenance:
        return self.provenance.to_provenance()

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "abi_version": self.abi_version,
            "min_nodus_version": self.min_nodus_version,
            "capabilities": self.capabilities,
            "provenance": self.provenance.model_dump(),
            "surfaces": {
                "tools": [t.as_dict() for t in self.surfaces.tools],
            },
        }


def load_manifest(extension_dir: str) -> ExtensionManifest:
    """Load and validate the nodus-extension.json from *extension_dir*.

    Raises ManifestError if the file is missing, not valid JSON, or fails validation.
    Raises AbiError if the abi_version is unsupported.
    """
    path = pathlib.Path(extension_dir) / "nodus-extension.json"
    if not path.exists():
        raise ManifestError(
            f"nodus-extension.json not found in {extension_dir!r}", path=str(path)
        )
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"invalid JSON in {path}: {exc}", path=str(path)) from exc
    if not isinstance(raw, dict):
        raise ManifestError(f"manifest must be a JSON object, got {type(raw).__name__}", path=str(path))

    # Validate abi_version early for a better error message
    abi = raw.get("abi_version", "1")
    if str(abi) not in _SUPPORTED_ABI_VERSIONS:
        raise AbiError(
            f"unsupported abi_version {abi!r}; supported: {sorted(_SUPPORTED_ABI_VERSIONS)}",
            abi_version=str(abi),
        )
    try:
        return ExtensionManifest.model_validate(raw)
    except Exception as exc:
        raise ManifestError(f"manifest validation failed: {exc}", path=str(path)) from exc
