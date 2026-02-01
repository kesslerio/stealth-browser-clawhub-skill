#!/usr/bin/env python3
"""
Nodriver stealth browser fetch.
Bypasses basic Cloudflare and anti-bot detection.

Usage:
    python nodriver-fetch.py "https://example.com" [options]

Options:
    --wait N          Wait N seconds after page load (default: 5)
    --screenshot FILE Save screenshot to file
    --output FILE     Save HTML to file
    --proxy URL       Use proxy (http://user:pass@host:port)
    --headless        Run headless (less stealthy, not recommended)
"""

import asyncio
import argparse
import sys
import json

try:
    import nodriver as n
except ImportError:
    print("Error: nodriver not installed. Run: pip install nodriver")
    sys.exit(1)


async def fetch_page(url: str, wait: int = 5, screenshot: str = None, 
                     output: str = None, proxy: str = None, headless: bool = False):
    """Fetch a page using nodriver stealth browser."""
    
    # Configure browser
    browser_args = []
    if proxy:
        browser_args.append(f"--proxy-server={proxy}")
    
    print(f"🥷 Starting nodriver browser...")
    browser = await n.start(
        headless=headless,
        browser_args=browser_args if browser_args else None
    )
    
    try:
        print(f"📡 Navigating to: {url}")
        page = await browser.get(url)
        
        # Wait for Cloudflare/anti-bot to resolve
        print(f"⏳ Waiting {wait}s for page to fully load...")
        await page.sleep(wait)
        
        # Get page info
        title = await page.evaluate("document.title")
        print(f"📄 Page title: {title}")
        
        # Check for common block indicators
        content = await page.get_content()
        if "Access Denied" in content or "blocked" in content.lower():
            print("⚠️  Warning: Page may be blocked. Try Camoufox or residential proxy.")
        
        # Screenshot
        if screenshot:
            await page.save_screenshot(screenshot)
            print(f"📸 Screenshot saved: {screenshot}")
        
        # Save HTML
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"💾 HTML saved: {output}")
        
        # Output to stdout if no file specified
        if not output:
            # Just print summary, not full HTML
            print(f"\n✅ Success! Page loaded ({len(content)} bytes)")
            print(f"   URL: {await page.evaluate('window.location.href')}")
        
        return content
        
    finally:
        await browser.stop()
        print("🛑 Browser closed")


def main():
    parser = argparse.ArgumentParser(description="Nodriver stealth browser fetch")
    parser.add_argument("url", help="URL to fetch")
    parser.add_argument("--wait", type=int, default=5, help="Wait time in seconds (default: 5)")
    parser.add_argument("--screenshot", help="Save screenshot to file")
    parser.add_argument("--output", help="Save HTML to file")
    parser.add_argument("--proxy", help="Proxy URL (http://user:pass@host:port)")
    parser.add_argument("--headless", action="store_true", help="Run headless (less stealthy)")
    
    args = parser.parse_args()
    
    # Run async
    n.loop().run_until_complete(
        fetch_page(
            url=args.url,
            wait=args.wait,
            screenshot=args.screenshot,
            output=args.output,
            proxy=args.proxy,
            headless=args.headless
        )
    )


if __name__ == "__main__":
    main()
