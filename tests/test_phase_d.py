"""Phase D: SubprocessRunner — spawn, invoke, teardown, timeout, worker protocol."""
from __future__ import annotations

import io
import json
import pathlib
import pytest

FIXTURE_DIR = pathlib.Path(__file__).parent / "fixtures" / "hello-ext"


class TestWorkerProtocol:
    """Test the worker message loop directly (no subprocess)."""

    def _run(self, messages: list[dict]) -> list[dict]:
        from nodus_extension.worker import _REGISTRY, run_loop
        _REGISTRY.clear()

        from nodus_extension.worker import register_tool
        register_tool("test.echo", lambda args: args.get("msg", ""))
        register_tool("test.fail", lambda args: (_ for _ in ()).throw(ValueError("boom")))

        stdin_lines = "\n".join(json.dumps(m) for m in messages) + "\n"
        stdin = io.StringIO(stdin_lines)
        stdout = io.StringIO()
        run_loop(stdin=stdin, stdout=stdout)
        results = []
        for line in stdout.getvalue().splitlines():
            line = line.strip()
            if line:
                results.append(json.loads(line))
        return results

    def test_echo_tool(self):
        results = self._run([
            {"id": "1", "op": "invoke", "name": "test.echo", "args": {"msg": "hello"}},
            {"op": "shutdown"},
        ])
        assert len(results) == 1
        assert results[0] == {"id": "1", "ok": True, "result": "hello"}

    def test_unknown_tool_returns_error(self):
        results = self._run([
            {"id": "2", "op": "invoke", "name": "test.nonexistent", "args": {}},
            {"op": "shutdown"},
        ])
        assert results[0]["ok"] is False
        assert "not found" in results[0]["error"]

    def test_handler_exception_returns_error(self):
        results = self._run([
            {"id": "3", "op": "invoke", "name": "test.fail", "args": {}},
            {"op": "shutdown"},
        ])
        assert results[0]["ok"] is False
        assert "boom" in results[0]["error"]

    def test_unknown_op_returns_error(self):
        results = self._run([
            {"id": "4", "op": "unknown_op"},
            {"op": "shutdown"},
        ])
        assert results[0]["ok"] is False

    def test_shutdown_exits_loop(self):
        results = self._run([{"op": "shutdown"}])
        assert results == []

    def test_empty_lines_ignored(self):
        from nodus_extension.worker import _REGISTRY, run_loop, register_tool
        _REGISTRY.clear()
        register_tool("test.echo", lambda args: args.get("msg", ""))
        stdin = io.StringIO("\n\n\n" + json.dumps({"id": "1", "op": "invoke", "name": "test.echo", "args": {"msg": "x"}}) + "\n" + json.dumps({"op": "shutdown"}) + "\n")
        stdout = io.StringIO()
        run_loop(stdin=stdin, stdout=stdout)
        results = [json.loads(l) for l in stdout.getvalue().splitlines() if l.strip()]
        assert len(results) == 1
        assert results[0]["ok"] is True


class TestSubprocessRunner:
    def _make_runner(self, timeout_s: float = 10.0) -> "SubprocessRunner":
        from nodus_extension.runner.subprocess import SubprocessRunner
        from nodus_extension.manifest import load_manifest
        manifest = load_manifest(str(FIXTURE_DIR))
        return SubprocessRunner(str(FIXTURE_DIR), manifest, timeout_s=timeout_s)

    def test_start_and_is_alive(self):
        runner = self._make_runner()
        try:
            runner.start()
            assert runner.is_alive()
        finally:
            runner.stop()

    def test_stop_cleans_up(self):
        runner = self._make_runner()
        runner.start()
        runner.stop()
        assert not runner.is_alive()

    def test_invoke_round_trip(self):
        runner = self._make_runner()
        try:
            runner.start()
            result = runner.invoke("test.hello.greet", {"name": "World"})
            assert result == "Hello, World!"
        finally:
            runner.stop()

    def test_invoke_unknown_tool_raises(self):
        from nodus_extension.errors import InvokeError
        runner = self._make_runner()
        try:
            runner.start()
            with pytest.raises(InvokeError):
                runner.invoke("nonexistent.tool", {})
        finally:
            runner.stop()

    def test_invoke_on_stopped_runner_raises(self):
        from nodus_extension.errors import SandboxError
        runner = self._make_runner()
        with pytest.raises(SandboxError, match="not running"):
            runner.invoke("test.hello.greet", {"name": "X"})

    def test_stop_twice_is_safe(self):
        runner = self._make_runner()
        runner.start()
        runner.stop()
        runner.stop()  # no exception

    def test_missing_entry_point_raises_sandbox_error(self, tmp_path):
        from nodus_extension.runner.subprocess import SubprocessRunner
        from nodus_extension.manifest import load_manifest
        from nodus_extension.errors import SandboxError
        import json
        (tmp_path / "nodus-extension.json").write_text(json.dumps({
            "name": "test.empty", "version": "1.0.0", "description": "no entry",
        }))
        manifest = load_manifest(str(tmp_path))
        runner = SubprocessRunner(str(tmp_path), manifest)
        with pytest.raises(SandboxError, match="entry point not found"):
            runner.start()

    def test_timeout_raises(self, tmp_path):
        from nodus_extension.errors import TimeoutError
        import json

        src_root = str(pathlib.Path(__file__).parent.parent / "src")
        (tmp_path / "nodus-extension.json").write_text(json.dumps({
            "name": "test.slow", "version": "1.0.0", "description": "slow extension",
        }))
        (tmp_path / "extension.py").write_text(
            f'import sys\nsys.path.insert(0, {src_root!r})\n'
            f'from nodus_extension.worker import register_tool, run_loop\n'
            f'import time\n'
            f'register_tool("test.slow.hang", lambda args: time.sleep(60))\n'
            f'run_loop()\n'
        )
        from nodus_extension.runner.subprocess import SubprocessRunner
        from nodus_extension.manifest import load_manifest
        manifest = load_manifest(str(tmp_path))
        runner = SubprocessRunner(str(tmp_path), manifest, timeout_s=0.5)
        try:
            runner.start()
            with pytest.raises(TimeoutError):
                runner.invoke("test.slow.hang", {})
        finally:
            runner.stop()
