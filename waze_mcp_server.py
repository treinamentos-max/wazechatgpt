"""
waze_mcp_server.py
==================

MCP server exposing the OpenWeb Ninja Waze API as tools. Built on FastMCP from the
official `mcp` SDK. Reuses WazeClient from `openweb_ninja_waze.py` (same folder).
"""

from typing import Any, Callable, Dict, Optional

from mcp.server.fastmcp import FastMCP

from openweb_ninja_waze import WazeClient, WazeAPIError

# Load OPENWEB_NINJA_API_KEY (and any other vars) from a .env file sitting next to this
# script, if one exists. Existing environment variables take precedence, so a host that
# injects the key via its own `env` block still wins over the .env file.
try:
    from pathlib import Path

    from dotenv import load_dotenv

    load_dotenv(Path(__file__).with_name(".env"))
except ImportError:
    pass

mcp = FastMCP("waze")

# Client is created lazily so importing this module (e.g. for `mcp install` /
# `mcp dev` introspection) never requires the API key.
_client: Optional[WazeClient] = None


def _get_client() -> WazeClient:
    global _client
    if _client is None:
        _client = WazeClient()  # reads OPENWEB_NINJA_API_KEY from the environment
    return _client


def _safe(call: Callable[[], Any]) -> Any:
    """Run a client call, converting API errors into a clean dict the model can read."""
    try:
        return call()
    except WazeAPIError as exc:
        return {"error": exc.message, "status_code": exc.status_code}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


@mcp.tool()
def get_traffic_alerts_and_jams(
    bottom_left_lat: float,
    bottom_left_lng: float,
    top_right_lat: float,
    top_right_lng: float,
    max_alerts: int = 20,
    max_jams: int = 20,
    alert_types: Optional[str] = None,
) -> Dict[str, Any]:
    """Get real-time Waze traffic alerts and jams inside a geographic rectangle.

    The rectangle is defined by two corners: bottom-left (south-west) and
    top-right (north-east). The bottom-left latitude and longitude must both be
    SMALLER than the corresponding top-right values.

    Args:
        bottom_left_lat: Latitude of the bottom-left (south-west) corner.
        bottom_left_lng: Longitude of the bottom-left (south-west) corner.
        top_right_lat: Latitude of the top-right (north-east) corner.
        top_right_lng: Longitude of the top-right (north-east) corner.
        max_alerts: Maximum number of alerts to return.
        max_jams: Maximum number of traffic jams to return.
        alert_types: Optional comma-separated filter, e.g.
            "ACCIDENT,POLICE,HAZARD,ROAD_CLOSED,JAM". Omit for all types.

    Returns:
        Parsed JSON containing alerts and jams, or an {"error": ...} object.
    """
    return _safe(lambda: _get_client().alerts_and_jams(
        bottom_left=(bottom_left_lat, bottom_left_lng),
        top_right=(top_right_lat, top_right_lng),
        max_alerts=max_alerts,
        max_jams=max_jams,
        alert_types=alert_types,
    ))


@mcp.tool()
def get_driving_directions(
    source_lat: float,
    source_lng: float,
    destination_lat: float,
    destination_lng: float,
    return_route_coordinates: bool = False,
) -> Dict[str, Any]:
    """Get driving routes between two points, including alerts along each route.

    Args:
        source_lat: Latitude of the start point.
        source_lng: Longitude of the start point.
        destination_lat: Latitude of the destination.
        destination_lng: Longitude of the destination.
        return_route_coordinates: If true, include the full route geometry
            (large payload). Leave false unless you need to draw the route.

    Returns:
        Parsed JSON with the possible routes, or an {"error": ...} object.
    """
    return _safe(lambda: _get_client().driving_directions(
        source_coordinates=(source_lat, source_lng),
        destination_coordinates=(destination_lat, destination_lng),
        return_route_coordinates=return_route_coordinates,
    ))


@mcp.tool()
def search_venues(
    bottom_left_lat: float,
    bottom_left_lng: float,
    top_right_lat: float,
    top_right_lng: float,
    categories: Optional[str] = None,
) -> Dict[str, Any]:
    """Find venues / points of interest inside a geographic rectangle.

    The rectangle is defined by its bottom-left (south-west) and top-right
    (north-east) corners; bottom-left values must be smaller than top-right.

    Args:
        bottom_left_lat: Latitude of the bottom-left corner.
        bottom_left_lng: Longitude of the bottom-left corner.
        top_right_lat: Latitude of the top-right corner.
        top_right_lng: Longitude of the top-right corner.
        categories: Optional comma-separated category filter.

    Returns:
        Parsed JSON with venues, or an {"error": ...} object.
    """
    return _safe(lambda: _get_client().venues(
        bottom_left=(bottom_left_lat, bottom_left_lng),
        top_right=(top_right_lat, top_right_lng),
        categories=categories,
    ))


@mcp.tool()
def autocomplete_places(
    query: str,
    near_lat: float,
    near_lng: float,
    language: str = "en",
) -> Dict[str, Any]:
    """Autocomplete / type-ahead for places, addresses and points of interest.

    Useful for turning a partial place name into concrete results (and
    coordinates) that can then feed get_driving_directions.

    Args:
        query: The partial search text, e.g. "empire state".
        near_lat: Latitude to bias results toward.
        near_lng: Longitude to bias results toward.
        language: Language code for results (e.g. "en", "es", "he").

    Returns:
        Parsed JSON with suggestions, or an {"error": ...} object.
    """
    return _safe(lambda: _get_client().autocomplete(
        q=query,
        coordinates=(near_lat, near_lng),
        language=language,
    ))


if __name__ == "__main__":
    mcp.run(transport="stdio")
