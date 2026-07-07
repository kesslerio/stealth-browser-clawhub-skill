#!/usr/bin/env python3
"""Shared runtime detection and subprocess helpers for stealth-browser scripts."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


DEFAULT_DISTROBOX_CONTAINER = "pybox"
DEFAULT_DISTROBOX_PYTHON = "python3.14"
DEFAULT_OPENCLAW_CAMOUFOX_NIXOS = "/data/bin/camoufox-nixos"
OPENCLAW_CONTEXT_ENV_VARS = (
    "OPENCLAW_HOME",
    "OPENCLAW_STATE_DIR",
    "OPENCLAW_CONFIG_PATH",
    "OPENCLAW_CLI",
    "ALPHACLAW_ROOT_DIR",
    "ALPHACLAW_CAMOUFOX_BRIDGE_SOCKET",
)


@dataclass(frozen=True)
class BrowserRuntime:
    kind: str
    binary: str


@dataclass(frozen=True)
class RuntimeSelection:
    runtime: BrowserRuntime | None
    error_message: str | None = None


class BrowserRuntimeError(RuntimeError):
    """Raised when runtime selection or invocation fails."""


def _env_disabled(value: str) -> bool:
    return value.lower() in {"none", "disabled"}


def _env_false(value: str) -> bool:
    return value.lower() in {"0", "false", "no", "none", "disabled"}


def _resolve_binary(binary_name: str, env_var: str) -> str | None:
    override = os.environ.get(env_var)
    if override:
        if _env_disabled(override):
            return None
        return override
    return shutil.which(binary_name)


def _resolve_openclaw_bridge_binary() -> str | None:
    bridge = os.environ.get(
        "STEALTH_BROWSER_OPENCLAW_CAMOUFOX_NIXOS_BIN",
        DEFAULT_OPENCLAW_CAMOUFOX_NIXOS,
    )
    if not bridge or _env_disabled(bridge):
        return None
    if os.path.isfile(bridge) and os.access(bridge, os.X_OK):
        return bridge
    return None


def _openclaw_context_enabled() -> bool:
    override = os.environ.get("STEALTH_BROWSER_OPENCLAW_CONTEXT")
    if override is not None:
        return not _env_false(override)
    return any(os.environ.get(name) for name in OPENCLAW_CONTEXT_ENV_VARS)


def _same_binary(left: str, right: str) -> bool:
    try:
        return os.path.samefile(left, right)
    except OSError:
        return os.path.abspath(left) == os.path.abspath(right)


def _is_openclaw_bridge_runtime(runtime: BrowserRuntime) -> bool:
    bridge = _resolve_openclaw_bridge_binary()
    return bool(bridge and _same_binary(runtime.binary, bridge))


def _pybox_available(distrobox_binary: str) -> bool:
    try:
        result = subprocess.run(
            [distrobox_binary, "list"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return False
    if result.returncode != 0:
        return False
    return DEFAULT_DISTROBOX_CONTAINER in result.stdout


def find_host_native_runtime() -> BrowserRuntime | None:
    override = os.environ.get("STEALTH_BROWSER_CAMOUFOX_NIXOS_BIN")
    if override:
        if _env_disabled(override):
            return None
        return BrowserRuntime(kind="host-native", binary=override)

    bridge = _resolve_openclaw_bridge_binary() if _openclaw_context_enabled() else None
    binary = bridge or shutil.which("camoufox-nixos")
    if not binary:
        return None
    return BrowserRuntime(kind="host-native", binary=binary)


def find_distrobox_runtime() -> BrowserRuntime | None:
    binary = _resolve_binary("distrobox", "STEALTH_BROWSER_DISTROBOX_BIN")
    if not binary:
        return None
    if not _pybox_available(binary):
        return None
    return BrowserRuntime(kind="distrobox", binary=binary)


def detect_browser_runtime() -> RuntimeSelection:
    host_native = find_host_native_runtime()
    if host_native is not None:
        return RuntimeSelection(runtime=host_native)

    distrobox = find_distrobox_runtime()
    if distrobox is not None:
        return RuntimeSelection(runtime=distrobox)

    return RuntimeSelection(
        runtime=None,
        error_message=(
            "No supported browser runtime found. Install `camoufox-nixos` for the "
            "NixOS-native path, or install `distrobox` with a `pybox` container "
            "for the legacy fallback."
        ),
    )


def run_camoufox_nixos(
    runtime: BrowserRuntime,
    args: Sequence[str],
    extra_env: Mapping[str, str] | None = None,
) -> dict:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    if _is_openclaw_bridge_runtime(runtime):
        env.pop("CAMOUFOX_NIXOS_STATE_ROOT", None)
    try:
        result = subprocess.run(
            [runtime.binary, *args],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
    except FileNotFoundError as exc:
        raise BrowserRuntimeError(
            f"camoufox-nixos binary not found: {runtime.binary}"
        ) from exc
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    if not stdout:
        raise BrowserRuntimeError(stderr or "camoufox-nixos returned no JSON output.")

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise BrowserRuntimeError(
            f"camoufox-nixos returned non-JSON output: {stdout}"
        ) from exc

    if not isinstance(payload, dict):
        raise BrowserRuntimeError("camoufox-nixos returned an invalid JSON payload.")

    payload["_exitCode"] = result.returncode
    payload["_stderr"] = stderr
    return payload


def payload_error_message(payload: dict, default: str) -> str:
    error = payload.get("error")
    if isinstance(error, dict):
        message = error.get("message")
        if isinstance(message, str) and message:
            return message
    stderr = payload.get("_stderr")
    if isinstance(stderr, str) and stderr:
        return stderr
    return default


def require_ok(payload: dict, default: str) -> dict:
    if payload.get("ok") is True:
        return payload
    raise BrowserRuntimeError(payload_error_message(payload, default))


def _strip_runtime_args(argv: Sequence[str]) -> list[str]:
    sanitized: list[str] = []
    skip_next = False

    for arg in argv:
        if skip_next:
            skip_next = False
            continue
        if arg == "--runtime":
            skip_next = True
            continue
        if arg.startswith("--runtime="):
            continue
        sanitized.append(arg)

    return sanitized


def run_distrobox_fallback(script_path: Path, argv: Sequence[str], runtime: BrowserRuntime) -> int:
    sanitized_argv = _strip_runtime_args(argv)
    command = [
        runtime.binary,
        "enter",
        DEFAULT_DISTROBOX_CONTAINER,
        "--",
        DEFAULT_DISTROBOX_PYTHON,
        str(script_path),
        "--runtime",
        "legacy",
        *sanitized_argv,
    ]
    try:
        result = subprocess.run(command, check=False)
    except FileNotFoundError as exc:
        raise BrowserRuntimeError(
            f"distrobox binary not found: {runtime.binary}"
        ) from exc
    return result.returncode
