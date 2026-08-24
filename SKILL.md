---
name: camoufox-stealth-browser
homepage: https://github.com/kesslerio/camoufox-stealth-browser-clawhub-skill
description: Explicit-only stealth browser automation with Camoufox for hostile sites that block Browser Use (the browser-use skill), standard Playwright, or Selenium flows. Default to Browser Use for ordinary browsing, booking flows, calendars, forms, screenshots, and generic site testing. Use Camoufox only when the user explicitly asks for Camoufox, a stealth browser, bot bypass, anti-bot evasion, Cloudflare/Datadome bypass, persistent login/session reuse, or a target has already blocked the Browser Use lane. Browser lane only; API helpers are secondary.
metadata:
  openclaw:
    emoji: "🦊"
    requires:
      bins: []
      env: []
---

# Camoufox Stealth Browser 🦊

Default browser lane: Browser Use (the `browser-use` skill).

Do not use this skill for ordinary browser automation. Use Browser Use (the `browser-use` skill) first for normal browsing, appointment booking, dynamic calendars, forms, screenshots, accessibility snapshots, and generic site testing.

Use Camoufox only when one of these is true:

- The user explicitly asks for Camoufox.
- The user explicitly asks for a stealth browser, bot bypass, anti-bot evasion, Cloudflare bypass, Datadome bypass, or similar.
- Browser Use already reached the site and was blocked by anti-bot or fingerprinting defenses.
- The task requires a persistent hostile-site stealth session and the user accepts that tradeoff.

Camoufox is the hostile-site browser lane, not the default browser lane. If Browser Use is unavailable, report that directly instead of silently switching to Camoufox unless the user asked for stealth/bypass behavior.

## Why Camoufox

| Approach | Patch level | Typical weakness |
|----------|-------------|------------------|
| **Camoufox** | Browser/runtime | Harder to fingerprint with timing and JS consistency checks |
| undetected-chromedriver | JS/runtime glue | Timing and environment mismatches |
| puppeteer-stealth | JS injection | Patches land after page startup |
| playwright-stealth | JS injection | Same class of weakness |

## Runtime Selection

For explicit Camoufox workflows, the skill uses this order:

1. OpenClaw/AlphaClaw bridge at `/data/bin/camoufox-nixos`, when present
2. `camoufox-nixos` from `PATH`
3. `distrobox` with `pybox`
4. clear setup failure if neither exists

Inside OpenClaw/AlphaClaw, prefer `/data/bin/camoufox-nixos`. Do not override the scripts to use `/run/current-system/sw/bin/camoufox-nixos` unless you are deliberately diagnosing the direct host wrapper; in this environment that path can report misleading missing-venv errors such as `/data/.local/venvs/camoufox/bin/python`.

The repo still carries a separate `curl_cffi` helper, but it is not the primary routing target for this skill.

## Quick Start

### Browser workflows

The browser scripts self-detect runtime. Use them directly:

```bash
./scripts/camoufox-fetch.py "https://example.com" --headless

./scripts/camoufox-session.py \
  --profile economist \
  --status "https://www.economist.com"
```

Do not frame browser execution as "importing Camoufox into system Python" or "switching to the proper runtime." Run the wrapper scripts directly and let them choose the runtime.

## Runtime Failure Reporting

When browser execution fails, report the observed runtime failure first.

- If `camoufox-nixos` times out or exits before navigation, say it failed before page navigation and treat it as a host runtime launch issue until proven otherwise.
- Do not turn a wrapper startup failure into a target-site blocking diagnosis.
- Do not claim a "legacy Python path worked" unless you actually ran that exact path and verified success.
- If you suggest the distrobox fallback, present it as an alternate documented browser lane, not proof that system Python imports are the real problem.

### Optional fallback/API setup

If `camoufox-nixos` is missing, or if you need the `curl_cffi` lane, run:

```bash
bash scripts/setup.sh
```

That script configures the distrobox fallback when `pybox` is available and tells you what is missing when it is not.

If you just patched the host-local NixOS wrapper itself, remember that the live `camoufox-nixos` command does not change until the host runs:

```bash
sudo nixos-rebuild switch --flake /etc/nixos#nixos
```

## When To Use

- Standard Playwright or Selenium gets blocked
- The site shows Cloudflare challenge loops
- You need persistent authenticated browsing for hostile or paywalled sites
- You need actual stealth rather than generic browser automation
- You need login/session reuse on a host that already has `camoufox-nixos`

Do **not** use this skill for ordinary browsing or generic site testing. Use Browser Use (the `browser-use` skill) for that.

## Workflow Summary

### Protected-page fetch

```bash
./scripts/camoufox-fetch.py \
  "https://www.yelp.com/biz/example" \
  --headless \
  --wait 8 \
  --screenshot yelp.png \
  --output yelp.html
```

### Persistent session

```bash
# Interactive login
./scripts/camoufox-session.py \
  --profile airbnb \
  --login "https://www.airbnb.com/account-settings"

# Reuse saved session
./scripts/camoufox-session.py \
  --profile airbnb \
  --headless "https://www.airbnb.com/trips"

# Check session status
./scripts/camoufox-session.py \
  --profile airbnb \
  --status "https://www.airbnb.com"
```

## State Ownership

This skill owns **no durable state of its own**. Browser profile state belongs to the selected runtime:

- **OpenClaw/AlphaClaw bridge (`/data/bin/camoufox-nixos`)**: bridge-managed host state mapping
- **Host-native (`camoufox-nixos`)**: `~/.cache/camoufox-nixos`
- **Legacy distrobox fallback**: `~/.stealth-browser/profiles/<name>/`

Implications:

- Persistent session reuse still works in both lanes because the runtimes own their own profile/cache locations.
- `--import-cookies` is a legacy fallback feature. If you ask for it without the distrobox lane, the script fails clearly instead of pretending parity.
- `--export-cookies` continues to work.

## Gotchas

See [references/gotchas.md](references/gotchas.md) for the non-obvious footguns: runtime-framing mistakes, browser lane vs API helper confusion, headed-login expectations, Linux-only fallback assumptions, and host-native state-path differences.

## Secondary API Helper

`curl_cffi` remains in this repo as a secondary API-only helper. It is useful when:

- there is no browser interaction requirement
- you already know the API endpoint
- browser overhead would be wasted

It is not the primary skill contract. Current repo guidance for it is still the legacy distrobox path:

```bash
distrobox enter pybox -- python3.14 scripts/curl-api.py "https://api.example.com"
```

## Non-NixOS And Missing Runtime

- **NixOS hosts with `camoufox-nixos`**: browser lane is host-native by default
- **Other Linux hosts**: use the distrobox fallback
- **macOS / Windows**: `camoufox-nixos` is not the portability story; the repo’s portable browser guidance is still the distrobox fallback where available

This skill does **not** try to teach every machine how to recreate `camoufox-nixos`. That wrapper is host-specific, and the distrobox lane is the compatibility path where available.

## Proxy Reminder

For Airbnb, Yelp, Datadome, and similar targets:

- datacenter IPs often get blocked immediately
- residential or mobile proxies are usually required
- sticky sessions matter more than rotating every request

See [references/proxy-setup.md](references/proxy-setup.md).

## Remote / Headed Login Notes

Interactive login still needs a visible browser window regardless of runtime. If you are remote, use a display-capable setup such as:

- local desktop session
- SSH with display forwarding where supported
- VNC or similar remote desktop

On TTY-only or headless shell sessions, headed `camoufox-nixos open` should fail fast with `display_missing`. That is expected. Use `--headless` unless you intentionally attached a real display.

## Troubleshooting

| Problem | Meaning | What to do |
|---------|---------|------------|
| `No supported browser runtime found` | Neither `camoufox-nixos` nor valid distrobox fallback was detected | Install the host wrapper or configure distrobox plus pybox |
| `display_missing` | You tried a headed host-native launch on a session with no `DISPLAY` or `WAYLAND_DISPLAY` | This is expected on TTY-only hosts and remote shells; rerun with `--headless` or use a real graphical session |
| `camoufox-nixos` times out before navigation | Browser wrapper failed to launch cleanly on the host | Report it as a host runtime launch issue first; only discuss site blocking after the browser actually reaches the target |
| `--import-cookies requires the legacy distrobox fallback` | Host-native lane cannot honestly reproduce that legacy import flow | Use the fallback lane for that operation |
| Browser lane works but `curl-api.py` does not | `curl_cffi` lane is still legacy-path setup in this repo | Run `bash scripts/setup.sh` |
| Immediate block or challenge loop | Proxy quality or behavior issue | Use residential/mobile proxy and increase wait time |

## References

- [README.md](README.md) — repo overview
- [references/gotchas.md](references/gotchas.md) — recurring footguns and local assumptions
- [references/proxy-setup.md](references/proxy-setup.md) — proxy guidance
- [references/fingerprint-checks.md](references/fingerprint-checks.md) — anti-bot fingerprint categories
