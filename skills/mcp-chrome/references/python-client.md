# Python MCP Bridge Client

A reusable Python pattern for calling the MCP bridge from external scripts (not via Hermes native tools). The bridge uses streamable HTTP transport on `http://127.0.0.1:12306/mcp`.

## Client Implementation

```python
import json, urllib.request

MCP_URL = "http://127.0.0.1:12306/mcp"

def mcp_connect():
    """Initialize session, return session ID."""
    body = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                   "clientInfo": {"name": "my-script", "version": "1.0"}}
    }).encode()
    req = urllib.request.Request(
        MCP_URL, data=body,
        headers={"Content-Type": "application/json",
                 "Accept": "application/json, text/event-stream"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        sid = dict(resp.getheaders()).get("mcp-session-id", "")
        resp.read()
    return sid or None

def mcp_call(sid, method, params):
    """Call an MCP tool, return parsed result."""
    body = json.dumps({
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": method, "arguments": params}
    }).encode()
    req = urllib.request.Request(
        MCP_URL, data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": sid
        }
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode()
    
    # Parse SSE format
    for line in raw.split("\n"):
        line = line.strip()
        if line.startswith("data: "):
            return json.loads(line[6:])
    return None

def mcp_run_js(sid, tab_id, js_code, timeout=30000):
    """Execute JS in a tab and extract return value.
    
    WARNING: HTTP API does NOT support async/await!
    Use only synchronous code with explicit `return`.
    """
    result = mcp_call(sid, "chrome_javascript", {
        "tabId": tab_id, "code": js_code, "timeoutMs": timeout
    })
    if not result:
        return None
    try:
        text = result["result"]["content"][0]["text"]
        data = json.loads(text)                   # Outer: {"success":true,"result":"..."}
        inner = json.loads(data.get("result", "{}"))  # Inner: actual JS return value
        return inner
    except (KeyError, json.JSONDecodeError):
        return None

def mcp_get_windows_and_tabs(sid):
    """Get all Chrome windows and tabs."""
    return mcp_call(sid, "chrome_get_windows_and_tabs", {})

def mcp_navigate(sid, url, tab_id=None):
    """Open a URL. If tab_id is None, opens new tab."""
    params = {"url": url}
    if tab_id:
        params["tabId"] = tab_id
    return mcp_call(sid, "chrome_navigate", params)
```

## Response Parsing (Triple-nested JSON)

The MCP HTTP response uses SSE with triple-nested JSON:

```
event: message
data: {"result":{"content":[{"type":"text",
       "text":"{\"success\":true,\"tabId\":123,\"engine\":\"cdp\",
               \"result\":\"{\\\"ok\\\":true}\"}"}]}}
```

Extraction chain:
1. Parse SSE `data:` line → `mcp_result`
2. `mcp_result["result"]["content"][0]["text"]` → outer JSON string
3. `json.loads(text)` → `{"success":true, "result":"{\"ok\":true}"}`
4. `data["result"]` → actual JS return value (string)
5. `json.loads(data["result"])` → final parsed value

## Key Limitations

| Limitation | Impact | Workaround |
|-----------|--------|------------|
| No async/await | async functions return `undefined` | Use sync code with `return` |
| `return` required | Expression without `return` is lost | Always start with `return` |
| One session per process | Each initialize creates a transport | Keep the same SID for all calls |
| Timeout per call | Long operations (scrolling) may fail | Set `timeoutMs` generously |
