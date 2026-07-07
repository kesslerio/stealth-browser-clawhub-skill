#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIXTURES="$ROOT/tests/fixtures"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

export STEALTH_BROWSER_OPENCLAW_CAMOUFOX_NIXOS_BIN="$FIXTURES/fake_camoufox_nixos.py"
unset STEALTH_BROWSER_CAMOUFOX_NIXOS_BIN
export STEALTH_BROWSER_DISTROBOX_BIN=none

STATUS_OUT="$TMPDIR/status.stdout"
python3 "$ROOT/scripts/camoufox-session.py" \
  --profile smoke \
  --status \
  "https://example.com" >"$STATUS_OUT"

grep -q "Profile: smoke" "$STATUS_OUT"
grep -q "Stored cookies for example.com: 1" "$STATUS_OUT"

EXPORT_PATH="$TMPDIR/cookies.json"
python3 "$ROOT/scripts/camoufox-session.py" \
  --profile smoke \
  --headless \
  --export-cookies "$EXPORT_PATH" \
  "https://example.com" >"$TMPDIR/export.stdout"

grep -q "Exported 1 cookies" "$TMPDIR/export.stdout"
grep -q '"domain": "example.com"' "$EXPORT_PATH"

printf '[]\n' > "$TMPDIR/import.json"
set +e
python3 "$ROOT/scripts/camoufox-session.py" \
  --profile smoke \
  --import-cookies "$TMPDIR/import.json" \
  "https://example.com" >"$TMPDIR/import.stdout" 2>"$TMPDIR/import.stderr"
status=$?
set -e
test "$status" -eq 2
grep -q "requires the legacy distrobox fallback" "$TMPDIR/import.stderr"

export STEALTH_BROWSER_CAMOUFOX_NIXOS_BIN=none
export STEALTH_BROWSER_DISTROBOX_BIN="$FIXTURES/fake_distrobox.sh"
export FAKE_DISTROBOX_EXEC_TEXT="session fallback"
export FAKE_DISTROBOX_LOG="$TMPDIR/session-distrobox.log"

python3 "$ROOT/scripts/camoufox-session.py" \
  --profile smoke \
  --status \
  "https://example.com" >"$TMPDIR/fallback.stdout"

grep -q "FAKE DISTROBOX EXEC session fallback" "$TMPDIR/fallback.stdout"
grep -q -- "--runtime legacy" "$TMPDIR/session-distrobox.log"

python3 "$ROOT/scripts/camoufox-session.py" \
  --profile smoke \
  --status \
  --runtime auto \
  "https://example.com" >"$TMPDIR/fallback-explicit-runtime.stdout"

grep -q "FAKE DISTROBOX EXEC session fallback" "$TMPDIR/fallback-explicit-runtime.stdout"
grep -q -- "--runtime legacy --profile smoke --status https://example.com" "$TMPDIR/session-distrobox.log"
if grep -q -- "--runtime auto" "$TMPDIR/session-distrobox.log"; then
  echo "unexpected runtime auto flag leaked into distrobox fallback" >&2
  exit 1
fi

echo "camoufox-session adapter checks passed"
