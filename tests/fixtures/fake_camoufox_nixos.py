#!/usr/bin/env python3
"""Stub camoufox-nixos command for adapter tests."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def payload(command: str, data: dict | None = None, page: dict | None = None) -> dict:
    return {
        "ok": True,
        "command": command,
        "profile": "stub-profile",
        "sessionId": "sess_stub",
        "page": page or {
            "url": "https://example.com",
            "title": "Example Domain",
        },
        "data": data or {},
        "error": None,
    }


def main() -> int:
    args = sys.argv[1:]
    log_path = os.environ.get("FAKE_CAMOUFOX_LOG")
    if log_path:
        with Path(log_path).open("a", encoding="utf-8") as handle:
            state_root = os.environ.get("CAMOUFOX_NIXOS_STATE_ROOT", "")
            handle.write(f"state_root={state_root} args={' '.join(args)}\n")

    if not args:
        print(json.dumps({"ok": False, "command": "unknown", "data": {}, "error": {"message": "missing command"}}))
        return 1

    command = args[0]
    if command == "open":
        url = args[-1] if args else "https://example.com"
        print(json.dumps(payload("open", data={"headless": "--headless" in args}, page={"url": url, "title": "Example Domain"})))
        return 0

    if command == "eval":
        expression = args[-1]
        if "document.documentElement.outerHTML" in expression:
            result = "<html><head><title>Example Domain</title></head><body><div id='content'>fixture</div></body></html>"
        elif "Boolean(document.querySelector" in expression:
            result = False
        else:
            result = None
        print(json.dumps(payload("eval", data={"result": result})))
        return 0

    if command == "screenshot":
        output = Path(args[-1]).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"stub image")
        print(json.dumps(payload("screenshot", data={"output": str(output)})))
        return 0

    if command == "storage-state":
        output = Path(args[-1]).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(
                {
                    "cookies": [
                        {
                            "name": "sessionid",
                            "value": "stub",
                            "domain": "example.com",
                        }
                    ],
                    "origins": [],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(json.dumps(payload("storage-state", data={"output": str(output), "cookies": 1})))
        return 0

    if command == "close":
        print(json.dumps(payload("close", data={"closed": True})))
        return 0

    print(json.dumps({"ok": False, "command": command, "data": {}, "error": {"message": f"unsupported {command}"}}))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
