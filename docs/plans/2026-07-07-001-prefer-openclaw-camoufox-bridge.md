---
title: "Prefer OpenClaw Camoufox Bridge Runtime"
created: 2026-07-07
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
execution: code
product_contract_source: ce-plan-bootstrap
---

# Prefer OpenClaw Camoufox Bridge Runtime

## Goal Capsule

Fix the stealth-browser skill so OpenClaw/AlphaClaw Camoufox workflows prefer the working `/data/bin/camoufox-nixos` host bridge over the direct host `/run/current-system/sw/bin/camoufox-nixos` wrapper when both are visible. This prevents agents from diagnosing a missing `/data/.local/venvs/camoufox` runtime when the actual supported path is the bridge.

## Product Contract

Product Contract preservation: Product Contract unchanged.

Requirements:

- R1: Browser workflows that explicitly use Camoufox must select the OpenClaw bridge runtime first when `/data/bin/camoufox-nixos` is executable.
- R2: Explicit `STEALTH_BROWSER_CAMOUFOX_NIXOS_BIN` overrides must continue to win for tests and operator diagnostics, including `none` and `disabled`.
- R3: Non-OpenClaw hosts must keep the existing behavior of using `camoufox-nixos` from `PATH`, then distrobox `pybox` fallback.
- R4: Fetch/session scripts must not force temporary state in a way that breaks the OpenClaw bridge state mapping.
- R5: Skill docs must explain the OpenClaw bridge path and warn against using `/run/current-system/sw/bin/camoufox-nixos` inside OpenClaw.

Non-goals:

- Do not make direct Camoufox launch inside AlphaClaw containers work.
- Do not rebuild NixOS or create `/data/.local/venvs/camoufox`.
- Do not change native OpenClaw Chromium browser behavior.

## Existing Patterns

- Runtime detection lives in `scripts/runtime_support.py`.
- Fetch adapter behavior is covered by `tests/camoufox-fetch-adapter.sh`.
- Runtime selection behavior is covered by `tests/runtime-selection.sh`.
- Discovery/docs expectations are covered by `scripts/test-discovery.sh` and `tests/discovery-cases.txt`.
- `SKILL.md` already distinguishes native OpenClaw browser from explicit Camoufox workflows.

## Implementation Units

### U1. Prefer Bridge Runtime

Files:

- `scripts/runtime_support.py`
- `tests/runtime-selection.sh`

Approach:

- Add an OpenClaw bridge candidate before generic `shutil.which("camoufox-nixos")`.
- Prefer `/data/bin/camoufox-nixos` only when it exists and is executable.
- Preserve `STEALTH_BROWSER_CAMOUFOX_NIXOS_BIN` as the highest-priority explicit override.
- Keep `none` and `disabled` override behavior.

Test scenarios:

- With no override and an executable fake bridge path, runtime selection returns that bridge binary.
- With an explicit override, runtime selection returns the override instead of the bridge.
- With the override set to `none`, runtime selection skips host-native and falls back to distrobox.

### U2. Preserve Bridge State Mapping

Files:

- `scripts/camoufox-fetch.py`
- `scripts/camoufox-session.py`
- `tests/camoufox-fetch-adapter.sh`
- `tests/camoufox-session-adapter.sh`

Approach:

- Avoid forcing `CAMOUFOX_NIXOS_STATE_ROOT` for host-native runtime unless needed for an isolated non-bridge test path.
- Let `/data/bin/camoufox-nixos` apply its own bridge defaults for container-to-host state mapping.
- Keep cleanup behavior for sessions opened by the scripts.

Test scenarios:

- Fetch via a fake bridge receives no forced temporary `CAMOUFOX_NIXOS_STATE_ROOT`.
- Fetch still writes HTML and screenshots through the host-native adapter.
- Session adapter still opens, evaluates, and closes via fake runtime.

### U3. Document OpenClaw Runtime Choice

Files:

- `SKILL.md`
- `README.md`
- `references/gotchas.md`
- `tests/discovery-cases.txt`

Approach:

- Add concise OpenClaw-specific guidance: use `/data/bin/camoufox-nixos` bridge inside OpenClaw/AlphaClaw.
- Explain that `/run/current-system/sw/bin/camoufox-nixos` may be a direct host wrapper and can report misleading missing-venv errors in this environment.
- Keep the existing “native browser first, Camoufox only explicitly” guidance.

Test scenarios:

- Discovery checks still pass.
- Docs contain the bridge guidance without making Camoufox look like the default browser lane.

## Verification

- `tests/runtime-selection.sh`
- `tests/camoufox-fetch-adapter.sh`
- `tests/camoufox-session-adapter.sh`
- `scripts/test-discovery.sh`
- Manual smoke: `PATH=/data/bin:$PATH ./scripts/camoufox-fetch.py https://example.com --headless --wait 0 --output /tmp/camoufox_fetch_bridge_test.html`

## Risks

- Over-preferring `/data/bin/camoufox-nixos` outside OpenClaw would be surprising if a developer happens to have that path mounted for another purpose. Limit preference to executable existence and preserve explicit override escape hatches.
- Removing temporary state injection can affect tests that assumed isolation. Update fake-runtime tests to assert the intended bridge contract rather than relying on temp state.
