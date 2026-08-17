from __future__ import annotations

from nodus_extension.capabilities import Capability, CapabilityGate
from nodus_extension.errors import (
    AbiError,
    CapabilityError,
    ExtensionError,
    InvokeError,
    ManifestError,
    RegistryError,
    SandboxError,
    TimeoutError,
)
from nodus_extension.host import ExtensionHost
from nodus_extension.manifest import ExtensionManifest, ToolSurface, load_manifest
from nodus_extension.nodus_bindings import attach_to_runtime
from nodus_extension.provenance import Origin, OwnerClass, Provenance, TrustClass
from nodus_extension.registry import ExtensionRegistry

__version__ = "0.1.1"

__all__ = [
    # Core
    "ExtensionRegistry",
    "ExtensionHost",
    "ExtensionManifest",
    "ToolSurface",
    "load_manifest",
    # Capabilities
    "Capability",
    "CapabilityGate",
    # Provenance
    "Provenance",
    "Origin",
    "TrustClass",
    "OwnerClass",
    # Bindings
    "attach_to_runtime",
    # Errors
    "ExtensionError",
    "ManifestError",
    "CapabilityError",
    "SandboxError",
    "AbiError",
    "RegistryError",
    "InvokeError",
    "TimeoutError",
    # Version
    "__version__",
]
