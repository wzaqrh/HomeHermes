---
name: mcp-chrome
description: Use the local Chrome MCP bridge to control the user's real Chrome session through the hangwin/mcp-chrome extension and bridge. Use when the user wants browser automation, page inspection, screenshots, tab management, or to work against the current Chrome profile and tabs.
version: 1.3.0
metadata:
  hermes:
    tags: [browser, chrome, mcp, automation, tabs, screenshots]
    related_skills: [native-mcp]
---

# mcp-chrome

Use this skill when you need to interact with the user's Chrome browser through the local `mcp-chrome-bridge` service and the installed Chrome extension.

## Key Principles

- **ALWAYS consult existing reports first** — before touching bridge or Chrome, check `~/reports/mcp-chrome-*.md` for prior fix solutions. The user expects you to learn from past debugging before trying random approaches. Dont start experimenting until you have read what was already figured out.
- **The bridge auto-starts with Chrome** — when Chrome launches with the extension installed and enabled, the bridge starts automatically on port 12306. Do NOT run `mcp-chrome-bridge start` — its not a valid command.
- **Hermes built-in browser tools** (browser_navigate, browser_click, etc.) are a viable alternative for navigation, form filling, and page reading. They work independently of the Chrome MCP bridge and dont require a running Chrome session.
- **The MCP server is a singleton** — the bridge `getMcpServer()` returns one `Server` instance that can only connect to one transport at a time. When the Chrome extension holds the connection via native messaging, any new MCP initialize attempt via HTTP returns Already connected to a transport. This does NOT mean the Hermes native MCP client is connected; it means the MCP server singleton is busy.
- **The HTTP server starts AFTER extension connects** — the bridge `index.js` calls `nativeHost.start()` (stdin reader) but NOT `server.start()`. The extension must send a type=start message via native messaging before port 12306 binds. Bridge process running does NOT mean HTTP server ready.
- **Use `ask-extension` for one-way commands when MCP is unavailable** — the bridge exposes a `GET /ask-extension` endpoint that sends arbitrary query params to the Chrome extension via the process_data message type. This works even when the MCP session is taken. HOWEVER, it only echoes back the query params in the response — it does NOT return page content, screenshots, or accessibility trees. Useful for navigation (`?action=chrome_navigate&url=...`) but not for reading the page.
- **Timing is critical** — Hermes native MCP client discovers tools ONLY at startup. If the bridge is down when Hermes starts, MCP tools will not register even if the bridge later comes up. The bridge must be alive BEFORE restarting Hermes.

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

### YAML (for Hermes Agent config.yaml)

Add to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  chrome:
    url: http://127.0.0.1:12306/mcp
```

Once added and Hermes is restarted, the native MCP client connects at startup and registers tools as `mcp_chrome_chrome_navigate`, `mcp_chrome_get_windows_and_tabs`, etc.

### JSON (for Codex CLI config.toml)

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

### Timing critical: Hermes must start AFTER bridge is alive

The native MCP client only discovers tools during startup. If the bridge isnt running when Hermes starts, the MCP tools will not be registered even if the bridge comes up later. Workarounds:
- Make sure bridge is running before restarting Hermes
- Or accept that MCP tools will be unavailable until next Hermes restart

### YAML (for Hermes Agent config.yaml)

Add to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  chrome:
    url: http://127.0.0.1:12306/mcp
```

Once added and Hermes is restarted, the native MCP client connects at startup and registers tools as `mcp_chrome_chrome_navigate`, `mcp_chrome_get_windows_and_tabs`, etc.

### JSON (for Codex CLI config.toml)

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

### Timing critical: Hermes must start AFTER bridge is alive

The native MCP client only discovers tools during startup. If the bridge isn't running when Hermes starts, the MCP tools won't be registered — even if the bridge comes up later. Workarounds:
- Make sure bridge is running before restarting Hermes
- Or accept that MCP tools won't be available until next Hermes restart

## Workflow

### Step 0 (CRITICAL): Consult existing reports first

Before touching the bridge or Chrome, check for existing fix reports:

```bash
ls ~/reports/mcp-chrome-*.md 2>/dev/null || echo "no reports"
cat ~/reports/mcp-chrome-mcp-fix-report.md 2>/dev/null
cat ~/reports/mcp-chrome-issue-summary.md 2>/dev/null
```

These reports document prior debugging sessions, known workarounds, and the singleton patch. Read them before attempting any fix or experiment. The Codex team already solved the disconnect/reconnect flow — do not re-derive it from scratch.

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
```

**Caution:** When Chrome starts normally (via desktop launcher or the extension's native messaging flow), port 9222 may be bound but does NOT expose standard CDP HTTP endpoints. Curling `/json/version` will return 404. This port is used internally by the MCP extension and is not directly accessible for CDP connections unless Chrome was explicitly launched with `--remote-debugging-port=9222`.

### Step 3a (bridge startup): HTTP server starts AFTER extension connects

The bridge binary starts the native messaging stdin reader immediately, but the HTTP server on port 12306 only binds when the Chrome extension sends the `start` message via native messaging. This means:

```
Bridge process running ↛ HTTP server ready
Extension sends 'start' → HTTP server binds port 12306
```

**Verification:** `curl -s http://127.0.0.1:12306/ping` must return `pong` before any MCP calls. If ping fails but the bridge process is running, the extension hasn't connected yet — open the extension popup and click Connect.

**After killing and restarting the bridge**, the extension's `nativeAutoConnectEnabled` might be `false` (persisted after a prior `DISCONNECT_NATIVE`). The popup's `ENSURE_NATIVE` message is NOT sufficient to re-enable auto-connect. The user must manually open the extension popup and click **Connect** (sends `CONNECT_NATIVE`).

### Step 5: Use the bridge

Once the bridge is running, use the native Hermes MCP client tools (if configured and auto-detected). If direct curl access is needed, initialize and capture the session ID:

```bash
# Initialize (capture session ID from response headers)
curl -s -i -X POST http://127.0.0.1:12306/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"hermes-agent","version":"1.0.0"}}}'

# Extract the mcp-session-id header from the response
SID=$(curl -s -i ... | grep -i 'mcp-session-id' | sed 's/.*: //' | tr -d '\r')

# Subsequent calls need the session ID header
curl -s -X POST http://127.0.0.1:12306/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"chrome_navigate","arguments":{"url":"https://example.com"}}}'
```

The initialize response includes headers:
- `mcp-session-id: <uuid>` — required for subsequent requests
- `content-type: text/event-stream` — responses use SSE format (event: message\ndata: {...}\n\n), not plain JSON

The streamable HTTP transport stores sessions in a server-side `transportsMap` (keyed by `mcp-session-id`). Sessions persist until the transport is explicitly closed or garbage-collected. Each curl invocation creates a new TCP connection; the session ID header is how the server finds the right transport.

### Alternative: Use Hermes built-in browser tools directly

For navigation, clicking, and form filling, Hermes built-in tools work without needing the MCP bridge:

- `browser_navigate(url)` — navigate to any URL
- `browser_snapshot()` — get page content with interactive element refs
- `browser_click(ref)` — click elements by ref ID
- `browser_type(ref, text)` — type into input fields
- `browser_vision(question)` — take screenshot and analyze visually

## Troubleshooting

### "Invalid MCP request or session."

Two possible causes:
1. **Session expired or never established on this connection** — the streamable HTTP transport tracks sessions via the `mcp-session-id` request header, stored in a server-side `transportsMap`. If you initialize on one HTTP connection and call a tool on a different one (or the session was garbage-collected), you get this error. Solution: keep the same HTTP connection for all calls in a session, or pass the `mcp-session-id` header from the initialize response to all subsequent requests.
2. **The Chrome extension needs reconnecting** — if the bridge restarted or the extension disconnected, the MCP session is gone. In the Chrome window, disconnect and reconnect the extension. The bridge auto-starts when the extension connects.

### "Already connected to a transport."

The bridge MCP server (`getMcpServer()`) is a **singleton** that supports only one transport connection at a time. This error means one transport is already active. Common scenarios:

- **The Chrome extension does NOT hold the MCP connection** — the extension uses native messaging (stdin/stdout), which is a separate path. The MCP server is not involved in extension-to-bridge communication unless an HTTP client initialized it first.
- **A previous initialize attempt held the session** — once any HTTP client initializes, the singleton is taken until that transport is closed.
- **Not necessarily the Hermes native MCP client** — unlike older versions of this skill suggested, this error often occurs when no native MCP client is configured. Check `config.yaml` for `mcp_servers`.

Workarounds:
- Use the `ask-extension` endpoint for one-way commands (navigation only, no page reading).
- Add `mcp_servers` to `~/.hermes/config.yaml` so Hermes connects at startup (before any curl attempts).
- Kill and restart the bridge process, then be the first client to initialize MCP.
- **Permanent fix: Patch the singleton** — edit `dist/mcp/mcp-server.js` to always create a fresh MCP server instead of reusing the singleton. See `references/bridge-architecture.md` for the patch. After patching, kill and restart the bridge.

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
| 9222 | Chrome internal | Bound but NOT standard CDP HTTP; returns 404 on all `/json/*` endpoints |
| 12306 | MCP Bridge | Streamable HTTP MCP endpoint at /mcp |

## Reference Files

- `references/bridge-architecture.md` — internal architecture details: singleton MCP server, session management, native messaging format, tool call flow, startup lifecycle
