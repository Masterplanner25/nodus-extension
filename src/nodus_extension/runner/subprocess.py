from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from nodus_extension.errors import InvokeError, SandboxError, TimeoutError
from nodus_extension.manifest import ExtensionManifest
from nodus_extension.runner.base import SandboxRunner

_DEFAULT_TIMEOUT_S = 30.0
_SHUTDOWN_WAIT_S = 2.0


class SubprocessRunner(SandboxRunner):
    """Sandbox tier 1: insecure-dev subprocess.

    Spawns the extension's extension.py in a child process and communicates
    over stdin/stdout using newline-delimited JSON (NDJSON).

    The extension must call nodus_extension.worker.run_loop() to enter the
    message loop. See nodus_extension.worker for the protocol.
    """

    def __init__(
        self,
        extension_dir: str,
        manifest: ExtensionManifest,
        timeout_s: float = _DEFAULT_TIMEOUT_S,
        python_executable: str | None = None,
    ) -> None:
        self._dir = Path(extension_dir)
        self._manifest = manifest
        self._timeout_s = timeout_s
        self._python = python_executable or sys.executable
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        entry = self._dir / "extension.py"
        if not entry.exists():
            raise SandboxError(
                f"extension entry point not found: {entry}. "
                f"Extension must have an extension.py file."
            )
        try:
            self._proc = subprocess.Popen(
                [self._python, str(entry)],
                cwd=str(self._dir),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except OSError as exc:
            raise SandboxError(f"failed to start extension subprocess: {exc}") from exc

    def stop(self) -> None:
        proc = self._proc
        if proc is None or proc.poll() is not None:
            return
        try:
            proc.stdin.write(json.dumps({"op": "shutdown"}) + "\n")
            proc.stdin.flush()
        except OSError:
            pass
        try:
            proc.wait(timeout=_SHUTDOWN_WAIT_S)
        except subprocess.TimeoutExpired:
            proc.kill()
        self._proc = None

    def invoke(self, tool_name: str, args: dict[str, Any]) -> Any:
        with self._lock:
            proc = self._proc
            if proc is None or proc.poll() is not None:
                raise SandboxError(
                    f"extension subprocess is not running (call start() first)"
                )
            msg_id = str(uuid.uuid4())
            request = json.dumps({"id": msg_id, "op": "invoke", "name": tool_name, "args": args})
            try:
                proc.stdin.write(request + "\n")
                proc.stdin.flush()
            except OSError as exc:
                raise SandboxError(f"failed to send invoke request: {exc}") from exc

            deadline = time.monotonic() + self._timeout_s
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(tool_name=tool_name, timeout_s=self._timeout_s)
                try:
                    line = self._readline_with_timeout(proc, remaining)
                except TimeoutError:
                    raise
                except OSError as exc:
                    raise SandboxError(f"subprocess stdout read error: {exc}") from exc
                if line is None:
                    raise SandboxError("extension subprocess closed stdout unexpectedly")
                line = line.strip()
                if not line:
                    continue
                try:
                    response = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if response.get("id") != msg_id:
                    continue
                if response.get("ok"):
                    return response.get("result")
                raise InvokeError(
                    response.get("error", "unknown error"), tool_name=tool_name
                )

    def is_alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def _readline_with_timeout(self, proc: subprocess.Popen, timeout_s: float) -> str | None:
        result: list[str | None] = [None]
        exc_holder: list[Exception | None] = [None]

        def reader():
            try:
                line = proc.stdout.readline()
                result[0] = line if line else None
            except Exception as e:
                exc_holder[0] = e

        t = threading.Thread(target=reader, daemon=True)
        t.start()
        t.join(timeout=timeout_s)
        if t.is_alive():
            raise TimeoutError(timeout_s=timeout_s)
        if exc_holder[0]:
            raise exc_holder[0]
        return result[0]
