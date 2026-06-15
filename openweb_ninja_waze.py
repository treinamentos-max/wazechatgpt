"""
openweb_ninja_waze.py
=====================

A lightweight Python client for the OpenWeb Ninja Waze API
(real-time traffic alerts, jams, driving directions, venues, and autocomplete).

Auth: the API key is sent in the ``x-api-key`` header.
Get a key: https://app.openwebninja.com/api/waze
"""

from __future__ import annotations

import os
from typing import Any, Dict, Iterable, Optional, Sequence, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://api.openwebninja.com/waze"

# A coordinate may be given as a "lat,lng" string or a (lat, lng) tuple/list.
Coordinate = Union[str, Sequence[float]]


class WazeAPIError(Exception):
    """Raised when the Waze API returns a non-2xx response."""

    def __init__(self, status_code: int, message: str, payload: Any = None) -> None:
        super().__init__(f"[{status_code}] {message}")
        self.status_code = status_code
        self.message = message
        self.payload = payload


def _fmt_coord(coord: Coordinate) -> str:
    """Normalize a coordinate to the ``"lat,lng"`` string the API expects."""
    if isinstance(coord, str):
        return coord.replace(" ", "")
    try:
        lat, lng = coord  # type: ignore[misc]
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"Coordinate must be a 'lat,lng' string or a (lat, lng) pair, got: {coord!r}"
        ) from exc
    return f"{lat},{lng}"


def _csv(value: Union[str, Iterable[str]]) -> str:
    """Turn a list/tuple of strings into a comma-separated string (pass strings through)."""
    if isinstance(value, str):
        return value
    return ",".join(str(v) for v in value)


class WazeClient:
    """Thin wrapper around the OpenWeb Ninja Waze REST endpoints."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = BASE_URL,
        timeout: float = 30.0,
        max_retries: int = 3,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENWEB_NINJA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Pass api_key=... or set the "
                "OPENWEB_NINJA_API_KEY environment variable."
            )

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update({"x-api-key": self.api_key})

        if max_retries:
            retry = Retry(
                total=max_retries,
                backoff_factor=0.5,
                status_forcelist=(429, 500, 502, 503, 504),
                allowed_methods=frozenset({"GET"}),
                raise_on_status=False,
            )
            adapter = HTTPAdapter(max_retries=retry)
            self.session.mount("https://", adapter)
            self.session.mount("http://", adapter)

    def _get(self, path: str, params: Dict[str, Any]) -> Any:
        cleaned: Dict[str, Any] = {}
        for key, value in params.items():
            if value is None:
                continue
            cleaned[key] = str(value).lower() if isinstance(value, bool) else value

        url = f"{self.base_url}/{path.lstrip('/')}"
        resp = self.session.get(url, params=cleaned, timeout=self.timeout)

        if not resp.ok:
            payload: Any = None
            message = resp.text
            try:
                payload = resp.json()
                if isinstance(payload, dict):
                    message = payload.get("message") or payload.get("error") or message
            except ValueError:
                pass
            raise WazeAPIError(resp.status_code, message, payload)

        return resp.json()

    def alerts_and_jams(
        self,
        bottom_left: Coordinate,
        top_right: Coordinate,
        *,
        center: Optional[Coordinate] = None,
        radius: Optional[float] = None,
        radius_units: Optional[str] = None,
        max_alerts: Optional[int] = None,
        max_jams: Optional[int] = None,
        alert_types: Optional[Union[str, Iterable[str]]] = None,
    ) -> Any:
        """Real-time alerts and jams inside a rectangle (bottom-left / top-right corners)."""
        return self._get(
            "alerts-and-jams",
            {
                "bottom_left": _fmt_coord(bottom_left),
                "top_right": _fmt_coord(top_right),
                "center": _fmt_coord(center) if center is not None else None,
                "radius": radius,
                "radius_units": radius_units,
                "max_alerts": max_alerts,
                "max_jams": max_jams,
                "alert_types": _csv(alert_types) if alert_types is not None else None,
            },
        )

    def driving_directions(
        self,
        source_coordinates: Coordinate,
        destination_coordinates: Coordinate,
        *,
        return_route_coordinates: Optional[bool] = None,
        arrival_timestamp: Optional[int] = None,
    ) -> Any:
        """Routes between two points, including alerts along each route."""
        return self._get(
            "driving-directions",
            {
                "source_coordinates": _fmt_coord(source_coordinates),
                "destination_coordinates": _fmt_coord(destination_coordinates),
                "return_route_coordinates": return_route_coordinates,
                "arrival_timestamp": arrival_timestamp,
            },
        )

    def venues(
        self,
        bottom_left: Coordinate,
        top_right: Coordinate,
        *,
        categories: Optional[Union[str, Iterable[str]]] = None,
        zoom_level: Optional[int] = None,
    ) -> Any:
        """Venues / POIs inside a rectangle (bottom-left / top-right corners)."""
        return self._get(
            "venues",
            {
                "bottom_left": _fmt_coord(bottom_left),
                "top_right": _fmt_coord(top_right),
                "categories": _csv(categories) if categories is not None else None,
                "zoom_level": zoom_level,
            },
        )

    def autocomplete(
        self,
        q: str,
        coordinates: Coordinate,
        *,
        language: Optional[str] = None,
    ) -> Any:
        """Type-ahead suggestions for places, locations and addresses."""
        return self._get(
            "autocomplete",
            {
                "q": q,
                "coordinates": _fmt_coord(coordinates),
                "language": language,
            },
        )
