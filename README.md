# Waze MCP Server

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server that exposes the
OpenWeb Ninja **Waze API** to LLM hosts (Claude Desktop, Claude Code, Cursor, or any custom
MCP client) as callable tools.

Each user supplies **their own** Waze API key at runtime via the `OPENWEB_NINJA_API_KEY`
environment variable — no key is bundled with the server.

## Tools

| Tool | What it does |
|---|---|
| `get_traffic_alerts_and_jams` | Real-time alerts (accident, police, hazard, road-closed…) and traffic jams inside a geographic rectangle. |
| `get_driving_directions` | Driving routes between two points, including alerts along each route. |
| `search_venues` | Venues / points of interest inside a geographic rectangle. |
| `autocomplete_places` | Type-ahead for places, addresses, and POIs (useful to turn text into coordinates before routing). |

All location inputs are plain latitude/longitude `float`s. Rectangles are defined by a
**bottom-left** (south-west) corner and a **top-right** (north-east) corner — the bottom-left
lat/lng must both be **smaller** than the top-right values.

## 1. Get an API key

Sign up (free tier available) and create a key at
**https://app.openwebninja.com/api/waze**. The key is sent in the `x-api-key` header by the
client; you provide it through the `OPENWEB_NINJA_API_KEY` environment variable.

You can supply it in either of two ways:

- **`.env` file** (handy for local dev): copy `.env.example` to `.env` and paste your key.
  The server auto-loads a `.env` sitting next to `waze_mcp_server.py`. **Never commit
  `.env`** — it is already in `.gitignore`.
- **Host `env` block** (recommended when connecting to a host): set it in the host config
  (see step 5). A key set in the host environment **overrides** the `.env` file.

## 2. Install

Requires **Python 3.10+**. Use an isolated environment so the dependencies don't conflict
with system packages.

### Option A — venv + pip

```bash
cd /path/to/WazeMCP
python3 -m venv .venv
. .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt   # or: pip install "mcp[cli]" requests
```

### Option B — uv (faster)

```bash
cd /path/to/WazeMCP
uv venv
uv pip install -r requirements.txt   # or: uv pip install "mcp[cli]" requests
```

Record the **absolute path** to the interpreter — you'll need it for the host config:

```bash
python3 -c "import sys; print(sys.executable)"
# e.g. /path/to/WazeMCP/.venv/bin/python
```

> `openweb_ninja_waze.py` and `waze_mcp_server.py` must stay in the **same folder** — the
> server imports the client.

## 3. Verify (offline, no key needed)

Confirm the install works and all 4 tools register — no API key or network required:

```bash
python3 -c "import asyncio, waze_mcp_server as s; print(len(asyncio.run(s.mcp.list_tools())), 'tools registered')"
# -> 4 tools registered
```

## 4. Try it live with the MCP Inspector (needs a real key)

```bash
export OPENWEB_NINJA_API_KEY="your_real_key"
mcp dev waze_mcp_server.py
```

In the browser UI, open **Tools**, pick `get_traffic_alerts_and_jams`, enter a small bounding
box (e.g. bottom-left `40.70, -74.02`, top-right `40.75, -73.96`), and run it. An
`{"error": ...}` object means something went wrong — read the message (commonly an invalid
key → 401, or an inverted bounding box).

## 5. Connect to a host

Each user puts **their own** key in the host's `env` block — not in the code.

### Claude Desktop

**Automatic:**

```bash
mcp install waze_mcp_server.py -v OPENWEB_NINJA_API_KEY=your_real_key
```

**Manual** — edit `claude_desktop_config.json` and use the **absolute path to the venv
interpreter** from step 2 (a bare `python` will likely fail):

```json
{
  "mcpServers": {
    "waze": {
      "command": "/path/to/WazeMCP/.venv/bin/python",
      "args": ["/path/to/WazeMCP/waze_mcp_server.py"],
      "env": { "OPENWEB_NINJA_API_KEY": "your_real_key" }
    }
  }
}
```

Config file locations:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Restart Claude Desktop, confirm the `waze` tools appear, then try a prompt that forces a
chain, e.g. *"Any accidents or police between Times Square and JFK right now?"* — the model
should call `autocomplete_places` → `get_driving_directions` → `get_traffic_alerts_and_jams`.

### Claude Code (CLI)

```bash
claude mcp add waze \
  -e OPENWEB_NINJA_API_KEY=your_real_key \
  -- /path/to/WazeMCP/.venv/bin/python /path/to/WazeMCP/waze_mcp_server.py
```

Or commit a project-scoped `.mcp.json` at the repo root:

```json
{
  "mcpServers": {
    "waze": {
      "command": "/path/to/WazeMCP/.venv/bin/python",
      "args": ["/path/to/WazeMCP/waze_mcp_server.py"],
      "env": { "OPENWEB_NINJA_API_KEY": "your_real_key" }
    }
  }
}
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'mcp'` | Server launched with an interpreter that lacks the deps | Point `command` at the venv interpreter where you installed `mcp`/`requests`. |
| `ModuleNotFoundError: No module named 'openweb_ninja_waze'` | Client file not alongside the server, or launched from another CWD | Keep both `.py` files in one folder. |
| `pip` error: `Cannot uninstall <pkg> ... installed by debian` | Installing into a system-managed Python | Use a venv or `uv`. |
| Tool returns `{"error": "...", "status_code": 401}` | Missing/invalid API key | Set `OPENWEB_NINJA_API_KEY` in the host's `env` block (not just your shell). |
| Empty results for a clearly busy area | Inverted bounding box | Ensure bottom-left lat/lng are both **smaller** than top-right. |
| Host shows no tools | Bad JSON in the config, or host not restarted | Validate the JSON; fully restart the host. |

## Files

- `openweb_ninja_waze.py` — thin HTTP client for the Waze REST API (auth, retries, coord formatting).
- `waze_mcp_server.py` — FastMCP server defining the 4 tools.
- `requirements.txt` — pinned runtime dependencies (`mcp[cli]`, `requests`).
- `.env.example` — template; copy to `.env` and add your key.
