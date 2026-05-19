# JavaScript Execution via MCP Bridge HTTP API

## Key Difference: Hermes Agent Tools vs HTTP API

| Channel | Supports async/await? | Returns |
|---------|----------------------|---------|
| Hermes native MCP tools (`mcp_chrome_chrome_javascript`) | Yes — auto-await | Promise resolution |
| HTTP API (`curl` / `urllib` / `requests` to port 12306) | **No** — returns `undefined` | Sync `return` statements only |

## HTTP API: Response Parsing

The HTTP API returns SSE format with triple-escaped JSON. To extract the JS result:

### Response structure

```
event: message
data: {"result":{"content":[{"type":"text","text":"{\"success\":true,\"tabId\":123,\"engine\":\"cdp\",\"result\":\"{\\\"ok\\\":true}\",\"metrics\":{\"elapsedMs\":7}}"}]},"isError":false,"jsonrpc":"2.0","id":2}
```

### Extraction steps (Python with `urllib`)

```python
import json, urllib.request

# 1. Connect and get session ID
body = json.dumps({
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {"protocolVersion": "2024-11-05", "capabilities": {},
               "clientInfo": {"name": "test", "version": "1.0"}}
}).encode()

req = urllib.request.Request(
    "http://127.0.0.1:12306/mcp",
    data=body,
    headers={"Content-Type": "application/json",
             "Accept": "application/json, text/event-stream"}
)
with urllib.request.urlopen(req, timeout=10) as resp:
    sid = dict(resp.getheaders()).get("mcp-session-id", "")
    resp.read()

# 2. Execute JavaScript (sync only!)
js_code = "return JSON.stringify({ok: true, ts: Date.now()})"
body = json.dumps({
    "jsonrpc": "2.0", "id": 2, "method": "tools/call",
    "params": {"name": "chrome_javascript",
               "arguments": {"tabId": 931908936, "code": js_code, "timeoutMs": 10000}}
}).encode()

req = urllib.request.Request(
    "http://127.0.0.1:12306/mcp",
    data=body,
    headers={
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "mcp-session-id": sid
    }
)
with urllib.request.urlopen(req, timeout=30) as resp:
    raw = resp.read().decode()

# 3. Parse the SSE response
for line in raw.split("\n"):
    line = line.strip()
    if line.startswith("data: "):
        mcp_result = json.loads(line[6:])  # Parse SSE data
        text = mcp_result["result"]["content"][0]["text"]  # Outer JSON string
        data = json.loads(text)  # Parse outer JSON
        result_str = data.get("result", "")  # This is the JS return value
        inner = json.loads(result_str)  # Parse JS return value
        print(inner)  # {"ok": true, "ts": ...}
        break
```

## Pitfalls

1. **Async functions return `undefined`** — the CDP `Runtime.evaluate` with `awaitPromise: false` (used by the HTTP bridge) returns the Promise object, not its resolved value. The Hermes native tools use `awaitPromise: true` and handle this internally.

2. **`return` is required** — without `return`, even a simple expression like `JSON.stringify({a:1})` returns `undefined`. Always start the code with `return` when using the HTTP API.

3. **Timeout** — set `timeoutMs` to a value appropriate for the task (default 10000). Complex synchronous operations may need longer.
