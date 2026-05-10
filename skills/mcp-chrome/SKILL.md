---
name: mcp-chrome
description: Use the local Chrome MCP bridge to control the user's real Chrome session through the hangwin/mcp-chrome extension and bridge. Use when the user wants browser automation, page inspection, screenshots, tab management, or to work against the current Chrome profile and tabs.
version: 1.1.0
metadata:
  hermes:
    tags: [browser, chrome, mcp, automation, tabs, screenshots]
    related_skills: [native-mcp]
---

# mcp-chrome

Use this skill when you need to interact with the user's Chrome browser through the local `mcp-chrome-bridge` service and the installed Chrome extension.

## Key Principles

- **The bridge auto-starts with Chrome** — when Chrome launches with the extension installed and enabled, the bridge starts automatically on port 12306. Do NOT run `mcp-chrome-bridge start` — it's not a valid command.
- **Hermes built-in browser tools** (browser_navigate, browser_click, etc.) are a viable alternative for navigation, form filling, and page reading. They work independently of the Chrome MCP bridge and don't require a running Chrome session.
- If the MCP bridge returns "Already connected to a transport" when called via curl, it means the native Hermes MCP client has already connected — this is expected and normal. Use the native MCP tools instead, or fall back to Hermes built-in browser tools.

## Assumptions

- The Chrome extension is installed and enabled.
- The native bridge is available as `mcp-chrome-bridge`.
- Chrome is installed on the system.

## Setup

If the bridge is not installed yet:

```bash
npm install -g mcp-chrome-bridge
```

If `pnpm` is used, enable postinstall scripts first or register manually:

```bash
pnpm config set enable-pre-post-scripts true
pnpm install -g mcp-chrome-bridge
```

Or:

```bash
pnpm install -g mcp-chrome-bridge
mcp-chrome-bridge register
```

## Hermes Configuration

Prefer the HTTP MCP endpoint:

```json
{
  "mcpServers": {
    "streamable-mcp-server": {
      "type": "streamable-http",
      "url": "http://127.0.0.1:12306/mcp"
    }
  }
}
```

## Workflow

### Step 1: Check if Chrome is running

```bash
pgrep -la chrome | head -5
```

### Step 2: Start Chrome if not running (with remote debugging)

```bash
google-chrome-stable --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.config/google-chrome" \
  --no-first-run --new-window <target-url> &>/dev/null & disown
```

**Important:** `--remote-debugging-port` requires `--user-data-dir` to be explicitly specified. Without it, Chrome silently ignores the flag.

If Chrome was already running without remote debugging, kill it first:
```bash
killall -9 chrome; sleep 2
# Then start fresh
```

### Step 3: Verify the bridge is alive

```bash
curl -s http://127.0.0.1:12306/ping
# Expected: {"status":"ok","message":"pong"}
```

### Step 4: Confirm DevTools port is accessible

```bash
ss -tlnp | grep 9222
curl -s http://127.0.0.1:9222/json/version | head -5
```

### Step 5: Use the bridge

Once the bridge is running, use the native Hermes MCP client tools (if configured and auto-detected). If direct curl access is needed, send initialize first:

```bash
curl -s -X POST http://127.0.0.1:12306/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"hermes-agent","version":"1.0.0"}}}'
```

### Alternative: Use Hermes built-in browser tools directly

For navigation, clicking, and form filling, Hermes built-in tools work without needing the MCP bridge:

- `browser_navigate(url)` — navigate to any URL
- `browser_snapshot()` — get page content with interactive element refs
- `browser_click(ref)` — click elements by ref ID
- `browser_type(ref, text)` — type into input fields
- `browser_vision(question)` — take screenshot and analyze visually

## Troubleshooting

### "Invalid MCP request or session."
The Chrome extension needs to be reconnected. In the Chrome window, disconnect and reconnect the extension. The bridge auto-starts when the extension connects.

### "Already connected to a transport."
This means the native Hermes MCP client has already established a connection. Don't try to connect via curl — use the native MCP tools (they should auto-discover as Hermes tools) or fall back to Hermes built-in browser tools.

### Port 9222 not binding after Chrome starts
Chrome detected an existing session and opened a new window there instead of creating a fresh instance. Fix:
```bash
killall -9 chrome
sleep 2
# Restart with explicit user-data-dir
```

### Bridge not starting (no pong on port 12306)
Chrome is not running, or the extension isn't loaded. Start Chrome first, the bridge auto-starts with the extension.

### doctor check shows everything OK but bridge not reachable
Chrome is not running. Start Chrome; the bridge auto-starts with the extension.

### Base common uses

- Get the current browser windows and tabs.
- Navigate to a URL in the existing Chrome session.
- Click, fill, and read page content from the active tab.
- Take screenshots of the current page.
- Inspect tabs, history, bookmarks, and network activity.

## Port Map

| Port | Service | Description |
|------|---------|-------------|
| 9222 | Chrome DevTools | Remote debugging protocol |
| 12306 | MCP Bridge | Streamable HTTP MCP endpoint at /mcp |
