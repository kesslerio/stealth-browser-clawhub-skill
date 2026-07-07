#!/usr/bin/env python3
"""
Camoufox stealth browser fetch.
Maximum anti-bot evasion - C++ level Firefox patches.
Best for: Yelp, Datadome, aggressive Cloudflare Turnstile.

Usage:
    ./scripts/camoufox-fetch.py "https://example.com" [options]

Options:
    --wait N          Wait N seconds after page load (default: 8)
    --screenshot FILE Save screenshot to file
    --output FILE     Save HTML to file
    --proxy URL       Use proxy (http://user:pass@host:port)
    --headless        Run headless (still stealthy with Camoufox)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from pathlib import Path

from runtime_support import (
    BrowserRuntimeError,
    detect_browser_runtime,
    payload_error_message,
    require_ok,
    run_camoufox_nixos,
    run_distrobox_fallback,
)


def print_runtime_error(message: str) -> int:
    print(f"Error: {message}", file=sys.stderr)
    return 1


def print_block_indicators(content: str) -> None:
    if "Access Denied" in content or "blocked" in content.lower():
        print("⚠️  Warning: Page may still be blocked. Check proxy quality.")
    elif "challenge" in content.lower() and "cloudflare" in content.lower():
        print("⚠️  Warning: Cloudflare challenge detected. Increase wait time.")
    else:
        print("✅ No obvious block indicators detected")


def fetch_page_legacy(
    url: str,
    wait: int = 8,
    screenshot: str | None = None,
    output: str | None = None,
    proxy: str | None = None,
    headless: bool = False,
) -> int:
    import asyncio
    from camoufox.async_api import AsyncCamoufox

    async def _run() -> int:
        print("🥷 Starting Camoufox browser (max stealth)...")

        config = {"headless": headless}
        if proxy:
            if "@" in proxy:
                auth_part = proxy.split("@")[0].replace("http://", "").replace("https://", "")
                host_part = proxy.split("@")[1]
                user, password = auth_part.split(":")
                host, port = host_part.split(":")
                config["proxy"] = {
                    "server": f"http://{host}:{port}",
                    "username": user,
                    "password": password,
                }
            else:
                config["proxy"] = {"server": proxy}

        async with AsyncCamoufox(**config) as browser:
            page = await browser.new_page()

            print(f"📡 Navigating to: {url}")
            await page.goto(url, wait_until="domcontentloaded")

            print(f"⏳ Waiting {wait}s for anti-bot resolution...")
            await asyncio.sleep(wait)

            title = await page.title()
            print(f"📄 Page title: {title}")

            content = await page.content()
            print_block_indicators(content)

            if screenshot:
                await page.screenshot(path=screenshot, full_page=True)
                print(f"📸 Screenshot saved: {screenshot}")

            if output:
                with open(output, "w", encoding="utf-8") as handle:
                    handle.write(content)
                print(f"💾 HTML saved: {output}")
            else:
                print(f"\n✅ Success! Page loaded ({len(content)} bytes)")
                print(f"   Final URL: {page.url}")

        return 0

    return asyncio.run(_run())


def fetch_page_host_native(
    url: str,
    wait: int = 8,
    screenshot: str | None = None,
    output: str | None = None,
    proxy: str | None = None,
    headless: bool = False,
) -> int:
    selection = detect_browser_runtime()
    runtime = selection.runtime
    if runtime is None:
        return print_runtime_error(selection.error_message or "No supported browser runtime found.")

    if runtime.kind != "host-native":
        return run_distrobox_fallback(Path(__file__).resolve(), sys.argv[1:], runtime)

    print("🥷 Starting Camoufox browser (NixOS-native runtime)...")

    profile = f"fetch-{uuid.uuid4().hex[:10]}"
    open_args = ["open", "--profile", profile]
    if headless:
        open_args.append("--headless")
    if proxy:
        open_args.extend(["--proxy", proxy])
    open_args.append(url)

    open_payload = run_camoufox_nixos(runtime, open_args)
    require_ok(open_payload, "Failed to open browser session.")
    session_id = open_payload.get("sessionId")
    if not isinstance(session_id, str) or not session_id:
        raise BrowserRuntimeError("camoufox-nixos did not return a session id.")

    try:
        print(f"📡 Navigating to: {url}")
        print(f"⏳ Waiting {wait}s for anti-bot resolution...")
        time.sleep(wait)

        eval_payload = run_camoufox_nixos(
            runtime,
            ["eval", "--session", session_id, "document.documentElement.outerHTML"],
        )
        require_ok(eval_payload, "Failed to read page HTML.")
        content = eval_payload.get("data", {}).get("result", "")
        if not isinstance(content, str):
            content = json.dumps(content)

        page = eval_payload.get("page") or open_payload.get("page") or {}
        title = page.get("title") or ""
        final_url = page.get("url") or url
        print(f"📄 Page title: {title}")
        print_block_indicators(content)

        if screenshot:
            screenshot_path = str(Path(screenshot).expanduser())
            screenshot_payload = run_camoufox_nixos(
                runtime,
                ["screenshot", "--session", session_id, screenshot_path],
            )
            require_ok(screenshot_payload, "Failed to capture screenshot.")
            print(f"📸 Screenshot saved: {screenshot_path}")

        if output:
            output_path = Path(output).expanduser()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
            print(f"💾 HTML saved: {output_path}")
        else:
            print(f"\n✅ Success! Page loaded ({len(content)} bytes)")
            print(f"   Final URL: {final_url}")

        return 0
    finally:
        close_payload = run_camoufox_nixos(
            runtime,
            ["close", "--session", session_id],
        )
        if close_payload.get("ok") is not True:
            message = payload_error_message(close_payload, "Failed to close browser session.")
            print(f"Warning: {message}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="Camoufox stealth browser fetch (max evasion)")
    parser.add_argument("url", help="URL to fetch")
    parser.add_argument("--wait", type=int, default=8, help="Wait time in seconds (default: 8)")
    parser.add_argument("--screenshot", help="Save screenshot to file")
    parser.add_argument("--output", help="Save HTML to file")
    parser.add_argument("--proxy", help="Proxy URL (http://user:pass@host:port)")
    parser.add_argument("--headless", action="store_true", help="Run headless")
    parser.add_argument("--runtime", choices=("auto", "legacy"), default="auto", help=argparse.SUPPRESS)

    args = parser.parse_args()

    try:
        if args.runtime == "legacy":
            return fetch_page_legacy(
                url=args.url,
                wait=args.wait,
                screenshot=args.screenshot,
                output=args.output,
                proxy=args.proxy,
                headless=args.headless,
            )

        return fetch_page_host_native(
            url=args.url,
            wait=args.wait,
            screenshot=args.screenshot,
            output=args.output,
            proxy=args.proxy,
            headless=args.headless,
        )
    except ImportError:
        return print_runtime_error("camoufox not installed in the selected legacy runtime.")
    except BrowserRuntimeError as exc:
        return print_runtime_error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
