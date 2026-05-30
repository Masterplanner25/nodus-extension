from __future__ import annotations

from typing import Any

from nodus_extension.errors import RegistryError
from nodus_extension.host import ExtensionHost
from nodus_extension.manifest import ExtensionManifest


class ExtensionRegistry:
    """Manages multiple loaded extensions.

    Typical usage:
        registry = ExtensionRegistry()
        registry.load("/path/to/my-ext")
        result = registry.invoke("myapp.my-extension", "myapp.greet", {"name": "Alice"})
        registry.unload("myapp.my-extension")
    """

    def __init__(self) -> None:
        self._hosts: dict[str, ExtensionHost] = {}

    def load(self, extension_dir: str, timeout_s: float = 30.0) -> ExtensionManifest:
        """Load an extension from *extension_dir*.

        Raises RegistryError if an extension with the same name is already loaded.
        Raises ManifestError, AbiError, SandboxError on load failures.
        """
        host = ExtensionHost(extension_dir, timeout_s=timeout_s)
        manifest = host.load()
        if manifest.name in self._hosts:
            host.unload()
            raise RegistryError(
                f"extension {manifest.name!r} is already loaded", name=manifest.name
            )
        self._hosts[manifest.name] = host
        return manifest

    def unload(self, name: str) -> None:
        """Unload the extension with *name*.

        Raises RegistryError if not loaded.
        """
        host = self._hosts.pop(name, None)
        if host is None:
            raise RegistryError(f"extension {name!r} is not loaded", name=name)
        host.unload()

    def list(self) -> list[dict]:
        """Return describe() for each loaded extension."""
        return [host.describe() for host in self._hosts.values()]

    def describe(self, name: str) -> dict | None:
        """Return describe() for the named extension, or None if not loaded."""
        host = self._hosts.get(name)
        return host.describe() if host is not None else None

    def invoke(self, name: str, tool_name: str, args: dict[str, Any] | None = None) -> Any:
        """Invoke *tool_name* in the named extension.

        Raises RegistryError if the extension is not loaded.
        Raises CapabilityError, InvokeError, TimeoutError on invocation failures.
        """
        host = self._hosts.get(name)
        if host is None:
            raise RegistryError(f"extension {name!r} is not loaded", name=name)
        return host.invoke(tool_name, args)

    def lookup(self, name: str) -> ExtensionHost | None:
        return self._hosts.get(name)

    def __len__(self) -> int:
        return len(self._hosts)

    def __contains__(self, name: str) -> bool:
        return name in self._hosts
