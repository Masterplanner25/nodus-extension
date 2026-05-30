from __future__ import annotations

import argparse
import json
import sys


def cmd_validate(args):
    from nodus_extension.manifest import load_manifest
    from nodus_extension import ManifestError, AbiError
    try:
        m = load_manifest(args.path)
        print(json.dumps(m.as_dict(), indent=2))
    except (ManifestError, AbiError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_describe(args):
    cmd_validate(args)


def cmd_load(args):
    from nodus_extension.registry import ExtensionRegistry
    r = ExtensionRegistry()
    try:
        m = r.load(args.path)
        print(json.dumps(m.as_dict(), indent=2))
        r.unload(m.name)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_invoke(args):
    from nodus_extension.registry import ExtensionRegistry
    r = ExtensionRegistry()
    try:
        m = r.load(args.path)
        ext_name = m.name
        try:
            tool_args = json.loads(args.args) if args.args else {}
        except json.JSONDecodeError:
            print(f"error: args is not valid JSON: {args.args!r}", file=sys.stderr)
            sys.exit(1)
        result = r.invoke(ext_name, args.tool, tool_args)
        print(json.dumps(result))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        try:
            r.unload(m.name)
        except Exception:
            pass


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="nodus-extension",
        description="nodus-extension CLI — manage and invoke Nodus extensions",
    )
    parser.add_argument("--version", action="version", version="nodus-extension 0.1.0")

    sub = parser.add_subparsers(dest="command", required=True)

    p_val = sub.add_parser("validate", help="Parse and validate a manifest")
    p_val.add_argument("path", help="Path to extension directory")
    p_val.set_defaults(func=cmd_validate)

    p_desc = sub.add_parser("describe", help="Display extension manifest (alias: validate)")
    p_desc.add_argument("path")
    p_desc.set_defaults(func=cmd_describe)

    p_load = sub.add_parser("load", help="Load extension and display manifest (then unload)")
    p_load.add_argument("path")
    p_load.set_defaults(func=cmd_load)

    p_inv = sub.add_parser("invoke", help="Load extension, invoke a tool, print result")
    p_inv.add_argument("path", help="Path to extension directory")
    p_inv.add_argument("tool", help="Tool name (dotted, e.g. myapp.greet)")
    p_inv.add_argument("args", nargs="?", default="{}", help="JSON args object")
    p_inv.set_defaults(func=cmd_invoke)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
