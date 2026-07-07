#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIXTURES="$ROOT/tests/fixtures"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

export STEALTH_BROWSER_OPENCLAW_CAMOUFOX_NIXOS_BIN="$FIXTURES/fake_camoufox_nixos.py"
unset STEALTH_BROWSER_CAMOUFOX_NIXOS_BIN
export STEALTH_BROWSER_DISTROBOX_BIN=none
export STEALTH_BROWSER_OPENCLAW_CONTEXT=1
export FAKE_CAMOUFOX_LOG="$TMPDIR/camoufox.log"
export CAMOUFOX_NIXOS_STATE_ROOT="$TMPDIR/stale-state-root"

HTML_OUT="$TMPDIR/page.html"
SHOT_OUT="$TMPDIR/page.png"
STDOUT_OUT="$TMPDIR/fetch.stdout"

python3 "$ROOT/scripts/camoufox-fetch.py" \
  "https://example.com" \
  --wait 0 \
  --output "$HTML_OUT" \
  --screenshot "$SHOT_OUT" \
  --headless >"$STDOUT_OUT"

grep -q "NixOS-native runtime" "$STDOUT_OUT"
grep -q "HTML saved" "$STDOUT_OUT"
grep -q "Example Domain" "$HTML_OUT"
test -s "$SHOT_OUT"
grep -q "state_root= args=open" "$FAKE_CAMOUFOX_LOG"
if grep -q "$TMPDIR/stale-state-root" "$FAKE_CAMOUFOX_LOG"; then
  echo "stale CAMOUFOX_NIXOS_STATE_ROOT leaked into bridge runtime" >&2
  exit 1
fi

export STEALTH_BROWSER_CAMOUFOX_NIXOS_BIN=none
export STEALTH_BROWSER_DISTROBOX_BIN="$FIXTURES/fake_distrobox.sh"
export FAKE_DISTROBOX_EXEC_TEXT="fetch fallback"
export FAKE_DISTROBOX_LOG="$TMPDIR/distrobox.log"

python3 "$ROOT/scripts/camoufox-fetch.py" "https://example.com" --wait 0 >"$TMPDIR/fallback.stdout"

grep -q "FAKE DISTROBOX EXEC fetch fallback" "$TMPDIR/fallback.stdout"
grep -q -- "--runtime legacy" "$TMPDIR/distrobox.log"

python3 "$ROOT/scripts/camoufox-fetch.py" \
  "https://example.com" \
  --wait 0 \
  --runtime auto >"$TMPDIR/fallback-explicit-runtime.stdout"

grep -q "FAKE DISTROBOX EXEC fetch fallback" "$TMPDIR/fallback-explicit-runtime.stdout"
grep -q -- "--runtime legacy https://example.com --wait 0" "$TMPDIR/distrobox.log"
if grep -q -- "--runtime auto" "$TMPDIR/distrobox.log"; then
  echo "unexpected runtime auto flag leaked into distrobox fallback" >&2
  exit 1
fi

echo "camoufox-fetch adapter checks passed"
