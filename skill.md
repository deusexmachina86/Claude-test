---
name: patchright-cli
description: Automates stealth browser interactions for web scraping, testing, form filling, screenshots, and data extraction with bot-detection bypass. Use when the user needs to navigate websites protected by Cloudflare, DataDome, or other anti-bot systems, interact with web pages, fill forms, take screenshots, test web applications, or extract information from web pages.
allowed-tools: Bash(patchright-cli:*)
---

# Browser Automation with patchright-cli

`patchright-cli` is powered by [Patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python) — a patched fork of Playwright that bypasses bot detection by avoiding the `Runtime.enable` CDP command that anti-bot systems (Cloudflare, DataDome, etc.) specifically watch for.

> **Note:** Only Chromium-based browsers are supported (`chrome`, `msedge`, `chromium`). Firefox and WebKit are not available.

## Installation

```bash
pip install patchright
patchright install chrome
pip install patchright-cli  # or: pip install -e . from repo root
```

## Quick start

```bash
# Open a new browser window
patchright-cli open

# Open and navigate right away
patchright-cli open https://example.com

# Navigate to a page
patchright-cli goto https://playwright.dev

# Interact with elements using refs from the snapshot
patchright-cli click e15
patchright-cli type "search query"
patchright-cli press Enter

# Take a screenshot (rarely needed — snapshot is more useful)
patchright-cli screenshot

# Close the browser
patchright-cli close
```

## Commands

### Core

```bash
patchright-cli open
patchright-cli open https://example.com
patchright-cli goto https://playwright.dev
patchright-cli type "search query"
patchright-cli click e3
patchright-cli dblclick e7
patchright-cli fill e5 "user@example.com"
patchright-cli drag e2 e8
patchright-cli hover e4
patchright-cli select e9 "option-value"
patchright-cli upload ./document.pdf e12
patchright-cli check e12
patchright-cli uncheck e12
patchright-cli snapshot
patchright-cli snapshot --filename=after-click.yaml
patchright-cli eval "document.title"
patchright-cli eval "el => el.textContent" e5
patchright-cli dialog-accept
patchright-cli dialog-accept "confirmation text"
patchright-cli dialog-dismiss
patchright-cli resize 1920 1080
patchright-cli close
```

### Navigation

```bash
patchright-cli go-back
patchright-cli go-forward
patchright-cli reload
```

### Keyboard

```bash
patchright-cli press Enter
patchright-cli press ArrowDown
patchright-cli keydown Shift
patchright-cli keyup Shift
```

### Mouse

```bash
patchright-cli mousemove 150 300
patchright-cli mousedown
patchright-cli mousedown right
patchright-cli mouseup
patchright-cli mouseup right
patchright-cli mousewheel 0 100
```

### Save As

```bash
patchright-cli screenshot
patchright-cli screenshot e5
patchright-cli screenshot --filename=page.png
patchright-cli pdf --filename=page.pdf
```

### Tabs

```bash
patchright-cli tab-list
patchright-cli tab-new
patchright-cli tab-new https://example.com/page
patchright-cli tab-close
patchright-cli tab-close 2
patchright-cli tab-select 0
```

### Storage

```bash
patchright-cli state-save
patchright-cli state-save auth.json
patchright-cli state-load auth.json
```

### Cookies

```bash
patchright-cli cookie-list
patchright-cli cookie-list --domain=example.com
patchright-cli cookie-get session_id
patchright-cli cookie-set session_id abc123
patchright-cli cookie-set session_id abc123 --domain=example.com --http-only --secure
patchright-cli cookie-delete session_id
patchright-cli cookie-clear
```

### LocalStorage

```bash
patchright-cli localstorage-list
patchright-cli localstorage-get theme
patchright-cli localstorage-set theme dark
patchright-cli localstorage-delete theme
patchright-cli localstorage-clear
```

### SessionStorage

```bash
patchright-cli sessionstorage-list
patchright-cli sessionstorage-get step
patchright-cli sessionstorage-set step 3
patchright-cli sessionstorage-delete step
patchright-cli sessionstorage-clear
```

### Network

```bash
patchright-cli route "/**/*.jpg" --status=404
patchright-cli route "https://api.example.com/" --body='{"mock": true}'
patchright-cli route-list
patchright-cli unroute "**/*.jpg"
patchright-cli unroute
```

### DevTools

```bash
patchright-cli console
patchright-cli console warning
patchright-cli network
patchright-cli run-code "document.querySelectorAll('a').length"
patchright-cli tracing-start
patchright-cli tracing-stop
patchright-cli video-stop video.webm
```

## Open parameters

```bash
# Use specific Chromium-based browser
patchright-cli open --browser=chrome      # default, recommended
patchright-cli open --browser=msedge
patchright-cli open --browser=chromium

# Run headless (may reduce stealth effectiveness)
patchright-cli open --headless

# Use a custom persistent profile directory
patchright-cli open --profile=/path/to/profile

# Close the browser
patchright-cli close

# Delete all user data for the session
patchright-cli delete-data
```

## Snapshots

After each command, `patchright-cli` prints a snapshot of the current browser state.

```
patchright-cli goto https://example.com

Page
  • Page URL: https://example.com/
  • Page Title: Example Domain
  • Tab [0] of 1

Snapshot
- main
  - heading "Example Domain"
  - paragraph
  - link "More information..." [e1]
```

You can also take a snapshot on demand:

```bash
patchright-cli snapshot
patchright-cli snapshot --filename=after-login.txt
```

## Browser Sessions

```bash
# Create a named session with a persistent profile
patchright-cli -s=mysession open https://example.com

# Use a specific profile directory
patchright-cli -s=mysession open https://example.com --profile=/path/to/profile

# Run commands in a named session
patchright-cli -s=mysession click e6
patchright-cli -s=mysession close

# Delete user data for a named session
patchright-cli -s=mysession delete-data

# List all active sessions
patchright-cli list

# Close all browsers
patchright-cli close-all

# Forcefully kill all browser processes
patchright-cli kill-all
```

You can also set the session via environment variable:

```bash
export PATCHRIGHT_SESSION=mysession
patchright-cli open https://example.com
patchright-cli click e3
```

## Stealth Tips

Patchright works best when:
- Using **Google Chrome** (`--browser=chrome`) rather than bare Chromium
- Running in **non-headless mode** (default) for sites with aggressive Cloudflare checks
- Combining with realistic delays and interaction patterns

## Examples

### Form submission

```bash
patchright-cli open https://example.com/form
patchright-cli snapshot
patchright-cli fill e1 "user@example.com"
patchright-cli fill e2 "password123"
patchright-cli click e3
patchright-cli snapshot
patchright-cli close
```

### Multi-tab workflow

```bash
patchright-cli open https://example.com
patchright-cli tab-new https://example.com/other
patchright-cli tab-list
patchright-cli tab-select 0
patchright-cli snapshot
patchright-cli close
```

### Debugging with DevTools

```bash
patchright-cli open https://example.com
patchright-cli click e4
patchright-cli fill e7 "test"
patchright-cli console
patchright-cli network
patchright-cli close
```

### Tracing

```bash
patchright-cli open https://example.com
patchright-cli tracing-start
patchright-cli click e4
patchright-cli fill e7 "test"
patchright-cli tracing-stop
patchright-cli close
```

### Bypassing Cloudflare (persistent session)

```bash
# First visit — browser window opens for CAPTCHA solving if needed
patchright-cli -s=cf open https://protected-site.com --profile=/tmp/cf-profile

# After solving the CAPTCHA, save the auth state
patchright-cli -s=cf state-save cf-auth.json

# Future sessions can load the saved state
patchright-cli -s=cf2 open https://protected-site.com --profile=/tmp/cf-profile2
patchright-cli -s=cf2 state-load cf-auth.json
```
