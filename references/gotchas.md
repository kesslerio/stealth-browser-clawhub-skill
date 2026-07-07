# Gotchas

These are the recurring footguns for this repo. They matter more than generic advice.

## Runtime Framing

- Do not say the browser lane failed because system Python cannot import the `camoufox` module.
- Do not narrate browser execution as "switching to the proper runtime."
- Run `./scripts/camoufox-fetch.py` or `./scripts/camoufox-session.py` directly.
- Inside OpenClaw/AlphaClaw, those wrapper scripts prefer `/data/bin/camoufox-nixos`, the host bridge client.
- Outside OpenClaw/AlphaClaw, those wrapper scripts detect `camoufox-nixos` from `PATH` first and fall back automatically when the legacy distrobox lane is valid.
- If the wrapper fails before page navigation, describe that as an observed host runtime launch failure.
- Do not infer that a legacy Python path worked unless you actually executed that exact path and verified success.
- Do not jump from wrapper startup failure to "site blocking" until the browser really reached the target page.
- Do not force `/run/current-system/sw/bin/camoufox-nixos` from OpenClaw unless you are deliberately diagnosing the direct host wrapper. It can bypass the bridge and produce misleading missing-venv errors such as `/data/.local/venvs/camoufox/bin/python`.

## Browser Lane Vs API Helper

- The primary skill contract is hostile-site browser automation.
- `curl_cffi` is still present, but it is a secondary API-only helper.
- If the task needs login, session reuse, page interaction, or anti-bot browser behavior, use the browser lane, not `curl-api.py`.

## State Ownership

- This skill owns no durable state.
- The OpenClaw/AlphaClaw bridge owns state mapping through `/data/bin/camoufox-nixos`; scripts should not override it with a temporary `CAMOUFOX_NIXOS_STATE_ROOT`.
- `camoufox-nixos` owns host-native browser state under `~/.cache/camoufox-nixos`.
- The legacy distrobox browser lane owns its own profile state under `~/.stealth-browser/profiles/<name>/`.
- Do not treat those runtime-owned directories as skill-managed state.

## Headed Login Expectations

- Interactive login still needs a visible browser window.
- `--login` is for headed manual session establishment, not headless auth magic.
- If you are remote, you still need a display-capable setup such as a local desktop session, forwarding that actually works, or VNC.
- On TTY-only or headless shell sessions, a headed host-native launch should fail with `display_missing` instead of pretending the browser lane is broken.

## NixOS Rebuilds

- If you patch the host-local `camoufox-nixos` NixOS module, the live wrapper does not update until `sudo nixos-rebuild switch --flake /etc/nixos#nixos` completes.
- Do not diagnose the old live wrapper before checking whether the rebuilt `/run/current-system/sw/bin/camoufox-nixos` actually points at the new store path.

## Fallback Assumptions

- The distrobox lane is a Linux compatibility path, not a universal cross-platform story.
- `camoufox-nixos` is host-specific. This repo does not explain how to recreate it on macOS or Windows.
- If neither `camoufox-nixos` nor distrobox + `pybox` exists, browser workflows should fail clearly instead of guessing.

## Legacy-Only Features

- `--import-cookies` is a legacy fallback feature.
- Do not assume the host-native browser lane can honestly reproduce every old distrobox-era storage trick.
- `--export-cookies` still works, but the storage model is different between runtimes.
