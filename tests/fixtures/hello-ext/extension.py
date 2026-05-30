"""Test extension: greets people by name."""
import sys
import os

# Allow importing nodus_extension from the project src/
_repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(_repo_root, "src"))

from nodus_extension.worker import register_tool, run_loop


def greet(args: dict) -> str:
    name = args.get("name", "World")
    return f"Hello, {name}!"


register_tool("test.hello.greet", greet)
run_loop()
