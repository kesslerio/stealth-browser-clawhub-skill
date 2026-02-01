---
name: stealth-browser
description: Anti-bot browser automation using Camoufox and Nodriver. Bypasses Cloudflare Turnstile, Datadome, and aggressive anti-bot on sites like Airbnb and Yelp. Use when standard Playwright/Selenium gets blocked.
metadata:
  openclaw:
    emoji: "🥷"
    requires:
      bins: ["distrobox"]
      env: []
---

# Stealth Browser Skill 🥷

Anti-bot browser automation that bypasses Cloudflare Turnstile, Datadome, and aggressive fingerprinting.

## When to Use

- Standard Playwright/Selenium gets blocked
- Site shows Cloudflare challenge or "checking your browser"
- Need to scrape Airbnb, Yelp, or similar protected sites
- `playwright-stealth` isn't working anymore

## Tool Selection

| Target Difficulty | Tool | When to Use |
|------------------|------|-------------|
| **Easy** | Nodriver | General Cloudflare, fast scraping |
| **Medium** | Patchright | Need Playwright API compatibility |
| **Hard** | Camoufox | Yelp, Datadome, aggressive Turnstile |
| **API Only** | curl_cffi | No browser needed, just TLS spoofing |

## Quick Start

All scripts run in `pybox` distrobox for isolation.

### 1. Setup (First Time)

```bash
# Install tools in pybox
distrobox-enter pybox -- pip install nodriver camoufox patchright curl_cffi

# Install Camoufox browser
distrobox-enter pybox -- python -c "import camoufox; camoufox.install()"
```

### 2. Fetch a Protected Page

**Nodriver (fast, general use):**
```bash
distrobox-enter pybox -- python scripts/nodriver-fetch.py "https://example.com"
```

**Camoufox (heavy-duty):**
```bash
distrobox-enter pybox -- python scripts/camoufox-fetch.py "https://example.com"
```

**API scraping (no browser):**
```bash
distrobox-enter pybox -- python scripts/curl-api.py "https://api.example.com/endpoint"
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     OpenClaw Agent                       │
├─────────────────────────────────────────────────────────┤
│  distrobox-enter pybox -- python scripts/xxx.py         │
├─────────────────────────────────────────────────────────┤
│                      pybox Container                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Nodriver   │  │  Camoufox   │  │  curl_cffi  │     │
│  │  (Chrome)   │  │  (Firefox)  │  │  (TLS spoof)│     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## Tool Details

### Nodriver
- **What:** Driverless Chrome automation (successor to undetected-chromedriver)
- **Pros:** Fast, no WebDriver protocol overhead, good Cloudflare bypass
- **Cons:** Less effective against Datadome/heavy fingerprinting
- **Best for:** Speed, general scraping, light Cloudflare

### Camoufox  
- **What:** Custom Firefox build with C++ level stealth patches
- **Pros:** Best fingerprint evasion, passes Turnstile automatically
- **Cons:** Heavier, Firefox-based (some sites prefer Chrome)
- **Best for:** Yelp, Datadome, aggressive anti-bot

### Patchright
- **What:** Playwright fork with stealth patches
- **Pros:** Drop-in Playwright replacement, familiar API
- **Cons:** Not as stealthy as Camoufox
- **Best for:** Existing Playwright code that needs stealth upgrade

### curl_cffi
- **What:** Python HTTP client with browser TLS fingerprint spoofing
- **Pros:** No browser overhead, very fast
- **Cons:** No JS execution, API endpoints only
- **Best for:** Known API endpoints, mobile app reverse engineering

## Critical: Proxy Requirements

**Datacenter IPs (AWS, DigitalOcean) = INSTANT BLOCK on Airbnb/Yelp**

You MUST use residential or mobile proxies:

```python
# Example proxy config
proxy = "http://user:pass@residential-proxy.example.com:8080"
```

See **[references/proxy-setup.md](references/proxy-setup.md)** for proxy configuration.

## Behavioral Tips

Sites like Airbnb/Yelp use behavioral analysis. To avoid detection:

1. **Warm up:** Don't hit target URL directly. Visit homepage first, scroll, click around.
2. **Mouse movements:** Inject random mouse movements (Camoufox/Nodriver handle this).
3. **Timing:** Add random delays (2-5s between actions), not fixed intervals.
4. **Session stickiness:** Use same proxy IP for 10-30 min sessions, don't rotate every request.

## Headless Mode Warning

⚠️ Old `--headless` flag is DETECTED. Options:

1. **New Headless:** Use `headless="new"` (Chrome 109+)
2. **Xvfb:** Run headed browser in virtual display
3. **Headed:** Just run headed if you can (most reliable)

```bash
# Xvfb approach (Linux)
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99
python scripts/camoufox-fetch.py "https://example.com"
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Access Denied" immediately | Use residential proxy |
| Cloudflare challenge loops | Try Camoufox instead of Nodriver |
| Browser crashes in pybox | Install missing deps: `sudo dnf install gtk3 libXt` |
| TLS fingerprint blocked | Use curl_cffi with `impersonate="chrome120"` |
| Turnstile checkbox appears | Add mouse movement, increase wait time |

## Examples

### Scrape Airbnb Listing

```bash
distrobox-enter pybox -- python scripts/nodriver-fetch.py \
  "https://www.airbnb.com/rooms/12345" \
  --wait 10 \
  --screenshot airbnb.png
```

### Scrape Yelp Business

```bash
distrobox-enter pybox -- python scripts/camoufox-fetch.py \
  "https://www.yelp.com/biz/some-restaurant" \
  --wait 8 \
  --output yelp.html
```

### API Scraping with TLS Spoofing

```bash
distrobox-enter pybox -- python scripts/curl-api.py \
  "https://api.yelp.com/v3/businesses/search?term=coffee&location=SF" \
  --headers '{"Authorization": "Bearer xxx"}'
```

## References

- [references/proxy-setup.md](references/proxy-setup.md) — Proxy configuration guide
- [references/fingerprint-checks.md](references/fingerprint-checks.md) — What anti-bot systems check
