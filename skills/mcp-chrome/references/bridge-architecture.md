# mcp-chrome-bridge Internal Architecture

## Process Flow

```
┌─────────────────────┐     Native Messaging (stdin/stdout)     ┌──────────────────┐
│  Chrome Extension   │ ◄─────────────────────────────────────► │  bridge process  │
│  (hangwin/mcp-chrome│     4-byte length + JSON message         │  (Node.js)       │
│   chrome-mcp-shared)│                                          │  port 12306      │
└─────────────────────┘                                          └────────┬─────────┘
                                                                         │
                                                                         │ HTTP MCP
                                                                         │ (streamable HTTP)
                                                                         ▼
                                                               ┌──────────────────┐
                                                               │  Hermes Agent     │
                                                               │  (or any MCP      │
                                                               │   client)         │
                                                               └──────────────────┘
```

## MCP Server: Singleton Limitation

File: `dist/mcp/mcp-server.js`

```javascript
exports.mcpServer = null;
const getMcpServer = () => {
    if (exports.mcpServer) return exports.mcpServer;  // ← singleton
    exports.mcpServer = new Server({...}, { capabilities: { tools: {} } });
    setupTools(exports.mcpServer);
    return exports.mcpServer;
};
```

**Patch to allow multiple connections:**

Edit `dist/mcp/mcp-server.js` to always create a fresh server instance instead of reusing the singleton:

```javascript
// BEFORE:
const getMcpServer = () => {
    if (exports.mcpServer) return exports.mcpServer;  // singleton
    exports.mcpServer = new Server({...});
    ...
};

// AFTER:
const getMcpServer = () => {
    // Always create fresh server per connection (bypass singleton guard)
    exports.mcpServer = new Server({...});
    ...
};
```

This allows each HTTP MCP initialize to get its own server transport. After patching, kill and restart the bridge for the change to take effect.

`getMcpServer()` returns one `Server` instance that can only connect to **one transport** at a time. The MCP SDK's `server.connect(transport)` sets the transport reference internally; calling it again while a transport is active raises "Already connected to a transport."

## Server Lifecycle

File: `dist/index.js`

```javascript
server.setNativeHost(nativeHost);
nativeHost.setServer(server);
nativeHost.start();              // ← starts stdin reader only
// NOTE: server.start() is NEVER called here!
```

The HTTP server (Fastify on port 12306) only starts when the Chrome extension sends a `start` message via native messaging, which triggers `nativeHost.startServer()`.

File: `dist/native-messaging-host.js`
```javascript
async startServer(port) {
    await this.associatedServer.start(port, this);
    this.sendMessage({
        type: NativeMessageType.SERVER_STARTED,
        payload: { port },
    });
}
```

## Tool Call Flow

When an MCP client calls a tool:

1. MCP client sends `tools/call` to `POST /mcp`
2. Server's `StreamableHTTPServerTransport.handleRequest()` processes it
3. `register-tools.js` `handleToolCall()` receives `{name, args}`
4. Native messaging sends to extension: `{name, args}` with type `CALL_TOOL`
5. Extension executes the tool in Chrome context
6. Response comes back via native messaging with `responseToRequestId` matching
7. Result is wrapped in MCP `{content: [{type: 'text', text: ...}]}` format

## Manual HTTP Server Startup

When the extension is disconnected, you can start the HTTP server programmatically by writing a native messaging `start` message to the bridge process stdin.

**Format:**
- 4 bytes: message length as UInt32LE (little-endian)
- N bytes: UTF-8 JSON payload

**Message payload:**
```json
{"type": "start", "payload": {"port": 12306}}
```

**Via /proc (Linux):**
```python
import struct, json
msg = json.dumps({"type": "start", "payload": {"port": 12306}})
raw = struct.pack("<I", len(msg)) + msg.encode()
with open(f"/proc/{pid}/fd/0", "wb") as f:
    f.write(raw)
```

**What happens:**
1. Bridge reads the message from stdin
2. `handleMessage()` matches `NativeMessageType.START`
3. Calls `nativeHost.startServer(port)` → `associatedServer.start(port, nativeHost)`
4. Fastify binds port 12306 and starts serving HTTP
5. Bridge sends `SERVER_STARTED` response to stdout (which goes nowhere since extension is disconnected)

**Limitation:** This only starts the HTTP server. The native messaging channel between bridge and extension is NOT established — the extension is still disconnected. Subsequent MCP tool calls (chrome_navigate, chrome_read_page, etc.) will time out because the bridge sends requests to stdout but no extension reads them.

## Recovery After `DISCONNECT_NATIVE`

When the user clicks Disconnect in the extension popup, the extension stores `nativeAutoConnectEnabled = false` persistently. The popup startup only sends `ENSURE_NATIVE`, which does NOT re-enable auto-connect.

**Fix (Codex report):** Edit the unpacked extension popup JS to send `CONNECT_NATIVE` instead of `ENSURE_NATIVE` on startup:
```js
// In .../chunks/popup-CaYPyESY.js
chrome.runtime.sendMessage({ type: NativeMessageType.CONNECT_NATIVE })
```

Without this fix, the user must manually open the extension popup and click Connect.

## Session Management

The `/mcp` POST handler uses `StreamableHTTPServerTransport` which tracks sessions via `transportsMap` (a `Map<sessionId, transport>`):

```javascript
this.transportsMap = new Map();
```

### Initialize (first request, no sessionId header):
```javascript
transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: () => newSessionId,
    onsessioninitialized: (id) => {
        this.transportsMap.set(id, transport);
    },
});
await getMcpServer().connect(transport);
```

### Subsequent calls (with mcp-session-id header):
```javascript
transport = this.transportsMap.get(sessionId);
await transport.handleRequest(request.raw, reply.raw, request.body);
```

### Response format:
- The `mcp-session-id` is returned as an HTTP **response header** (not in the body)
- Body uses SSE format: `event: message\ndata: {...}\n\n`
- SSE parsing: extract lines starting with `data: ` and JSON-parse the rest

### Session lifecycle:
- Created on first initialize (no sessionId header, body is an initialize request)
- Stored in `transportsMap` after `onsessioninitialized` fires
- Used for all subsequent requests with matching `mcp-session-id` header
- Destroyed when `transport.onclose` fires (bridge shutdown, timeout, or error)
- Each curl invocation is a separate TCP connection — session affinity is via the header only

### Header-based workflow:
```bash
# Step 1: Initialize (capture session ID from response)
SESSION_ID=$(curl -s -i -X POST http://127.0.0.1:12306/mcp ... \
  | grep -i 'mcp-session-id' | head -1 | sed 's/.*: //' | tr -d '\r')

# Step 2: Tool call (pass the session ID)
curl -s -X POST http://127.0.0.1:12306/mcp \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":...}'
```

## Tool Schemas

Exported from `chrome-mcp-shared`. Key tools available:

| Tool Name | Description |
|-----------|-------------|
| `get_windows_and_tabs` | List all open windows and tabs |
| `chrome_navigate` | Navigate to URL in active tab |
| `chrome_read_page` | Get accessibility tree of visible elements |
| `chrome_screenshot` | Take screenshot of current page |
| `chrome_computer` | Mouse/keyboard/screenshot actions |
| `chrome_javascript` | Execute JavaScript in page context |
| `chrome_click_element` | Click element by selector |
| `chrome_fill_or_select` | Fill input or select option |
| `chrome_get_web_content` | Fetch page HTML/content |
| `chrome_switch_tab` | Switch to tab by ID |
| `chrome_close_tabs` | Close one or more tabs |
| `chrome_history` | Browser history access |
| `chrome_bookmark_search` | Search bookmarks |
| `chrome_network_capture` | Capture network requests |
| `chrome_gif_recorder` | Record GIF of page interactions |

Flow tools (dynamic, from extension):
| `flow.<slug>` | User-recorded flows with variable inputs and run options |

## Available MCP Tools (from chrome-mcp-shared)

## /ask-extension Endpoint

`GET /ask-extension?key=value` sends `request.query` (the parsed query parameters) to the extension with message type `process_data`. The extension's `process_data` handler processes the query and returns a response.

This endpoint:
- Works regardless of MCP session state
- Returns the extension's response directly (not MCP-formatted)
- Only echoes query params back for standard tool names — it does NOT execute MCP tool calls
- Uses `PROCESS_DATA` message type (not `CALL_TOOL`), so it hits a different handler in the extension

## Port 9222 Behavior

When Chrome starts normally (without `--remote-debugging-port`), it still binds port 9222 but does NOT serve standard CDP endpoints:
- `/json` → 404
- `/json/version` → 404  
- `/json/list` → 404
- WebSocket upgrade → 403

This port is used internally, possibly by the DevTools frontend or the MCP extension. It is NOT useful for CDP-based automation via puppeteer, playwright, or CDP libraries when Chrome was started normally.

## Puppeteer and Profile Locking

The Chrome user data directory (`~/.config/google-chrome`) is locked by the running Chrome instance via a lockfile (`SingletonLock`). Attempting to launch puppeteer with `userDataDir` pointing to the same directory will fail with:

> "The browser is already running for /home/bdwillwin/.config/google-chrome. Use a different `userDataDir` or stop the running browser first."

Workarounds:
1. Kill Chrome first (`killall chrome`), then launch puppeteer with `userDataDir`
2. Copy the profile to a temp location (cookie encryption may break this)
3. Use the MCP bridge (which shares the same Chrome instance)

## Native Messaging Message Format

Chrome sends messages to the native host on stdin:
```
[4 bytes: message length as UInt32LE][N bytes: UTF-8 JSON message]
```

The native host sends responses back on stdout in the same format.
