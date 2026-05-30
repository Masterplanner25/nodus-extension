from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from nodus_extension.host import ExtensionHost


def register_extension_tools(runtime: Any, host: "ExtensionHost") -> None:
    """Register all tool surfaces from *host* in the NodusRuntime tool registry.

    Each tool surface declared in the extension's manifest is registered as a
    callable in `runtime.tool_registry`. The handler routes invocations through
    the extension's sandbox runner.

    Tags registered tools with extension provenance metadata.
    """
    manifest = host.manifest
    if manifest is None:
        return
    prov = manifest.provenance.model_dump()
    for surface in manifest.surfaces.tools:
        tool_name = surface.name

        def _make_handler(name: str) -> Any:
            return lambda args: host.invoke(name, args)

        runtime.tool_registry.register({
            "name": tool_name,
            "handler": _make_handler(tool_name),
            "description": surface.description,
            "schema": surface.schema_ or {},
            "version": surface.version,
            "metadata": {
                "extension_name": manifest.name,
                "extension_version": manifest.version,
                "abi_surface": f"tool/{surface.version}",
                "trust_class": prov.get("trust_class", "dev"),
                "origin": prov.get("origin", "local"),
            },
        })


def unregister_extension_tools(runtime: Any, host: "ExtensionHost") -> None:
    """Remove all tool surfaces from *host* from the NodusRuntime tool registry."""
    manifest = host.manifest
    if manifest is None:
        return
    for surface in manifest.surfaces.tools:
        try:
            runtime.tool_registry.unregister(surface.name)
        except (KeyError, Exception):
            pass
