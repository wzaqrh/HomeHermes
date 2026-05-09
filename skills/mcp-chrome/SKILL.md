---
name: mcp-chrome
description: Use the local Chrome MCP bridge to control the user's real Chrome session through the hangwin/mcp-chrome extension and bridge. Use when the user wants browser automation, page inspection, screenshots, tab management, or to work against the current Chrome profile and tabs.
version: 1.0.0
metadata:
  hermes:
    tags: [browser, chrome, mcp, automation, tabs, screenshots]
    related_skills: []
---

# mcp-chrome

Use this skill when you need to interact with the user's Chrome browser through the local `mcp-chrome-bridge` service and the installed Chrome extension.

## Assumptions

- The Chrome extension is installed and enabled.
- Chrome is running locally.
- The native bridge is available as `mcp-chrome-bridge`.

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

If something is broken, run:

```bash
mcp-chrome-bridge doctor
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

1. Confirm the bridge is installed and the extension is loaded in Chrome.
2. Use `mcp-chrome-bridge doctor` if the connection is not working.
3. Prefer the HTTP endpoint at `http://127.0.0.1:12306/mcp`.
4. Only use browser tools after confirming the current Chrome session is connected.

## Common Uses

- Get the current browser windows and tabs.
- Navigate to a URL in the existing Chrome session.
- Click, fill, and read page content from the active tab.
- Take screenshots of the current page.
- Inspect tabs, history, bookmarks, and network activity.

## Troubleshooting

- If tools do not appear, restart Hermes after adding the MCP config.
- If the port is busy, update the bridge port and match the Hermes config.
- If the bridge path is wrong, rerun `mcp-chrome-bridge doctor --fix`.
