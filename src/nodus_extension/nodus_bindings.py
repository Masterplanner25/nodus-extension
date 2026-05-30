from __future__ import annotations

import json
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from nodus_extension.registry import ExtensionRegistry

_PREFIX = "_ext_"


def attach_to_runtime(runtime: Any, registry: "ExtensionRegistry") -> None:
    """Register nodus-extension host functions on *runtime*, bound to *registry*.

    After calling this, Nodus scripts that import "nodus-extension" can call:
      ext_load(path)         → load an extension, returns its name
      ext_list()             → JSON string of loaded extension summaries
      ext_invoke(name, tool, args_json) → result as JSON string
      ext_describe(name)     → JSON string of extension details

    Parameters
    ----------
    runtime:
        A ``NodusRuntime`` instance.
    registry:
        The ``ExtensionRegistry`` that manages loaded extensions.
    """
    runtime.register_function(
        _PREFIX + "load",
        lambda path: _load(registry, path),
        arity=1,
    )
    runtime.register_function(
        _PREFIX + "list",
        lambda: json.dumps(registry.list()),
        arity=0,
    )
    runtime.register_function(
        _PREFIX + "invoke",
        lambda name, tool, args_json: _invoke(registry, name, tool, args_json),
        arity=3,
    )
    runtime.register_function(
        _PREFIX + "describe",
        lambda name: json.dumps(registry.describe(name)),
        arity=1,
    )


def _load(registry: "ExtensionRegistry", path: str) -> str:
    manifest = registry.load(path)
    return manifest.name


def _invoke(registry: "ExtensionRegistry", name: str, tool: str, args_json: str) -> str:
    try:
        args = json.loads(args_json) if args_json else {}
    except json.JSONDecodeError:
        args = {}
    result = registry.invoke(name, tool, args)
    return json.dumps(result)
