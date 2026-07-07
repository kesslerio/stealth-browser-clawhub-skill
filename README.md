# Camoufox Stealth Browser 🦊

Camoufox is the browser-stealth skill for hostile sites that block standard automation.

## Primary Use

Browser workflows are now:

1. `/data/bin/camoufox-nixos` first inside OpenClaw/AlphaClaw when that bridge exists
2. `camoufox-nixos` from `PATH` on NixOS hosts that have it
3. `distrobox` + `pybox` fallback on compatible Linux setups

This is the repo's primary promise. The `curl_cffi` helper still exists, but it is a secondary API-only lane rather than the main routing target.

## Browser Quick Start

```bash
./scripts/camoufox-fetch.py "https://example.com" --headless

./scripts/camoufox-session.py \
  --profile example \
  --status "https://example.com"
```

The browser scripts self-detect runtime. You do not need to decide between host-native and fallback manually, and you should not describe this as importing `camoufox` into system Python.

Inside OpenClaw/AlphaClaw, do not force `/run/current-system/sw/bin/camoufox-nixos` unless you are deliberately testing the direct host wrapper. The supported production path is the `/data/bin/camoufox-nixos` bridge, which maps container state to the host runtime.

## Setup

If `camoufox-nixos` is already installed, the browser lane is ready.

If you patched the underlying NixOS wrapper, the live `camoufox-nixos` command does not update until you rebuild the host system:

```bash
sudo nixos-rebuild switch --flake /etc/nixos#nixos
```

If it is missing, or if you also want the optional API helper lane, run:

```bash
bash scripts/setup.sh
```

That script configures the distrobox fallback when possible and tells you what is missing when it cannot.

## Runtime Matrix

| Use case | Preferred lane | Fallback |
|----------|----------------|----------|
| Browser automation inside OpenClaw/AlphaClaw | `/data/bin/camoufox-nixos` bridge | `distrobox` + `pybox` |
| Browser automation on NixOS host | `camoufox-nixos` | `distrobox` + `pybox` |
| Browser automation on other compatible Linux hosts | `distrobox` + `pybox` | none in this repo |
| API-only scraping | `curl_cffi` in distrobox | none in this repo |

## State Ownership

This skill owns no durable state. Browser state depends on the selected runtime:

- `camoufox-nixos`: `~/.cache/camoufox-nixos`
- OpenClaw/AlphaClaw bridge: host-side state mapped by `/data/bin/camoufox-nixos`
- legacy distrobox lane: `~/.stealth-browser/profiles/<name>/`

## Gotchas

Read [references/gotchas.md](references/gotchas.md) before assuming parity between the host-native browser lane and the legacy distrobox lane.

On TTY-only or headless shell sessions, a headed host-native launch should return `display_missing`. That is expected; use `--headless` unless a real display session is attached.

## Secondary API Helper

- `--export-cookies` still works.
- `--import-cookies` is a legacy fallback feature.
- `curl_cffi` stays available for API-only scraping, but it is not the main reason this skill exists.
- This repo does not try to make `camoufox-nixos` a generic cross-platform install target.

## Verification

Skill/package checks:

```bash
bash scripts/lint-skill.sh
bash scripts/test-discovery.sh
```

Browser adapter checks:

```bash
bash tests/runtime-selection.sh
bash tests/camoufox-fetch-adapter.sh
bash tests/camoufox-session-adapter.sh
```

## Docs

- [SKILL.md](SKILL.md) — full usage guide
- [references/gotchas.md](references/gotchas.md) — recurring footguns and local assumptions
- [references/proxy-setup.md](references/proxy-setup.md) — proxy guidance
- [references/fingerprint-checks.md](references/fingerprint-checks.md) — anti-bot fingerprint categories
