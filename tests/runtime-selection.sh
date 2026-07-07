#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIXTURES="$ROOT/tests/fixtures"

export PYTHONPATH="$ROOT/scripts"
export STEALTH_BROWSER_OPENCLAW_CAMOUFOX_NIXOS_BIN="$FIXTURES/fake_camoufox_nixos.py"
unset STEALTH_BROWSER_CAMOUFOX_NIXOS_BIN
export STEALTH_BROWSER_DISTROBOX_BIN="$FIXTURES/fake_distrobox.sh"

python3 - <<'PY'
from runtime_support import detect_browser_runtime

selection = detect_browser_runtime()
assert selection.runtime is not None
assert selection.runtime.kind == "host-native"
assert selection.runtime.binary.endswith("fake_camoufox_nixos.py")
PY

export STEALTH_BROWSER_CAMOUFOX_NIXOS_BIN="/tmp/explicit-camoufox-nixos"

python3 - <<'PY'
from runtime_support import detect_browser_runtime

selection = detect_browser_runtime()
assert selection.runtime is not None
assert selection.runtime.kind == "host-native"
assert selection.runtime.binary == "/tmp/explicit-camoufox-nixos"
PY

export STEALTH_BROWSER_CAMOUFOX_NIXOS_BIN=none

python3 - <<'PY'
from runtime_support import detect_browser_runtime

selection = detect_browser_runtime()
assert selection.runtime is not None
assert selection.runtime.kind == "distrobox"
PY

export FAKE_DISTROBOX_NO_PYBOX=1

python3 - <<'PY'
from runtime_support import detect_browser_runtime

selection = detect_browser_runtime()
assert selection.runtime is None
assert "camoufox-nixos" in selection.error_message
PY

echo "runtime selection checks passed"
