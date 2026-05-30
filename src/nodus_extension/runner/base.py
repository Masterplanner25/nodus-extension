from __future__ import annotations

import abc
from typing import Any


class SandboxRunner(abc.ABC):
    """Abstract base for extension sandbox runners.

    v0.1: SubprocessRunner (insecure-dev subprocess)
    v0.2+: DockerRunner (OCI container), VmRunner (strong-sandbox VM)
    """

    @abc.abstractmethod
    def start(self) -> None:
        """Start the sandbox. Raises SandboxError on failure."""

    @abc.abstractmethod
    def stop(self) -> None:
        """Stop the sandbox. Best-effort; should not raise."""

    @abc.abstractmethod
    def invoke(self, tool_name: str, args: dict[str, Any]) -> Any:
        """Invoke a tool inside the sandbox.

        Raises InvokeError if the tool fails.
        Raises TimeoutError if the invocation exceeds its deadline.
        Raises SandboxError if the runner is not started or crashes.
        """

    @abc.abstractmethod
    def is_alive(self) -> bool:
        """Return True if the sandbox process/container is running."""
