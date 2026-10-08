import os

from fastmcp import FastMCP
from fastmcp.server.auth.providers.github import GitHubProvider
import waze_mcp_server as waze

BASE_URL = "https://waze-chatgpt-waze.dxpacp.easypanel.host"
ALLOWED_USER = "treinamentos-max"


class PrivateGitHubProvider(GitHubProvider):
    async def verify_token(self, token):
        access = await super().verify_token(token)
        if access is None:
            return None

        login = str(access.claims.get("login", "")).casefold()
        if login != ALLOWED_USER.casefold():
            return None

        return access


auth = PrivateGitHubProvider(
    client_id=os.environ["GITHUB_CLIENT_ID"],
    client_secret=os.environ["GITHUB_CLIENT_SECRET"],
    base_url=BASE_URL,
    redirect_path="/auth/callback",
)

mcp = FastMCP("Waze ChatGPT", auth=auth)

for tool in (
    waze.get_traffic_alerts_and_jams,
    waze.get_driving_directions,
    waze.search_venues,
    waze.autocomplete_places,
):
    mcp.tool(
        tool,
        annotations={
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        path="/mcp",
        stateless_http=True,
        json_response=True,
    )
