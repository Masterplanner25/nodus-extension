from __future__ import annotations

from typing import Any

from nodus_extension.capabilities import Capability, CapabilityGate
from nodus_extension.errors import RegistryError, SandboxError
from nodus_extension.manifest import ExtensionManifest, load_manifest
from nodus_extension.runner.base import SandboxRunner
from nodus_extension.runner.subprocess import SubprocessRunner


class ExtensionHost:
    """Manages the lifecycle of a single extension.

    Responsibilities:
    - Load and validate the manifest
    - Create the sandbox runner (subprocess in v0.1)
    - Enforce capability gates before every invocation
    - Expose describe() for provenance and surface inventory
    """

    def __init__(self, extension_dir: str, timeout_s: float = 30.0) -> None:
        self._dir = extension_dir
        self._timeout_s = timeout_s
        self._manifest: ExtensionManifest | None = None
        self._gate: CapabilityGate | None = None
        self._runner: SandboxRunner | None = None
        self._loaded = False

    def load(self) -> ExtensionManifest:
        if self._loaded:
            raise RegistryError(
                "extension already loaded; call unload() first",
                name=self._manifest.name if self._manifest else None,
            )
        manifest = load_manifest(self._dir)
        gate = CapabilityGate.from_manifest_strings(
            manifest.capabilities, extension_name=manifest.name
        )
        runner = SubprocessRunner(self._dir, manifest, timeout_s=self._timeout_s)
        runner.start()
        self._manifest = manifest
        self._gate = gate
        self._runner = runner
        self._loaded = True
        return manifest

    def unload(self) -> None:
        if self._runner is not None:
            self._runner.stop()
        self._runner = None
        self._manifest = None
        self._gate = None
        self._loaded = False

    def invoke(self, tool_name: str, args: dict[str, Any] | None = None) -> Any:
        if not self._loaded or self._runner is None:
            raise SandboxError("extension is not loaded; call load() first")
        self._gate.require(Capability.tool_invoke)
        return self._runner.invoke(tool_name, args or {})

    def describe(self) -> dict:
        if self._manifest is None:
            return {}
        return {
            "name": self._manifest.name,
            "version": self._manifest.version,
            "description": self._manifest.description,
            "abi_version": self._manifest.abi_version,
            "capabilities": list(self._manifest.capabilities),
            "provenance": self._manifest.provenance.model_dump(),
            "tools": [t.as_dict() for t in self._manifest.surfaces.tools],
            "loaded": self._loaded,
        }

    @property
    def manifest(self) -> ExtensionManifest | None:
        return self._manifest

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def name(self) -> str | None:
        return self._manifest.name if self._manifest else None
