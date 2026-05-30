from __future__ import annotations


class ExtensionError(Exception):
    """Base class for all nodus-extension errors."""


class ManifestError(ExtensionError):
    """Raised when a manifest is missing, malformed, or fails validation."""

    def __init__(self, msg: str, path: str | None = None) -> None:
        super().__init__(msg)
        self.path = path


class CapabilityError(ExtensionError):
    """Raised when an extension attempts an operation it lacks capability for."""

    def __init__(self, capability: str, extension: str | None = None) -> None:
        msg = f"extension lacks capability: {capability!r}"
        if extension:
            msg = f"{extension!r} {msg}"
        super().__init__(msg)
        self.capability = capability
        self.extension = extension


class SandboxError(ExtensionError):
    """Raised when the sandbox runner encounters a lifecycle error."""


class AbiError(ExtensionError):
    """Raised when an extension declares an unsupported ABI version or surface."""

    def __init__(self, msg: str, abi_version: str | None = None) -> None:
        super().__init__(msg)
        self.abi_version = abi_version


class RegistryError(ExtensionError):
    """Raised for duplicate registration, missing extension, or load conflicts."""

    def __init__(self, msg: str, name: str | None = None) -> None:
        super().__init__(msg)
        self.name = name


class InvokeError(ExtensionError):
    """Raised when a tool invocation fails inside the extension worker."""

    def __init__(self, msg: str, tool_name: str | None = None) -> None:
        super().__init__(msg)
        self.tool_name = tool_name


class TimeoutError(ExtensionError):
    """Raised when an extension worker invocation exceeds its deadline."""

    def __init__(self, tool_name: str | None = None, timeout_s: float | None = None) -> None:
        parts = ["extension invoke timed out"]
        if tool_name:
            parts.append(f"tool={tool_name!r}")
        if timeout_s is not None:
            parts.append(f"after {timeout_s}s")
        super().__init__(", ".join(parts))
        self.tool_name = tool_name
        self.timeout_s = timeout_s
