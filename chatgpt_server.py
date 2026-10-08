"""Conexão HTTP das ferramentas Waze com o ChatGPT."""

import os

from waze_mcp_server import mcp

mcp.settings.host = os.getenv("MCP_HOST", "127.0.0.1")
mcp.settings.port = int(os.getenv("PORT", "8000"))
mcp.settings.streamable_http_path = "/mcp"
mcp.settings.stateless_http = True
mcp.settings.json_response = True

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
