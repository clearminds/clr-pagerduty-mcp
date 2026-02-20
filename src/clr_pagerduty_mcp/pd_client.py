"""REST client for PagerDuty API v2."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

API_BASE = "https://api.pagerduty.com"


class PagerDutyClient:
    """PagerDuty REST API v2 client with token auth.

    Attributes:
        api_key: The PagerDuty API token.
        email: Email address used for the ``From`` header in write operations.
    """

    def __init__(self, api_key: str, email: str = "") -> None:
        self.api_key = api_key
        self.email = email
        self._http = httpx.Client(
            base_url=API_BASE,
            timeout=15.0,
            headers={
                "Authorization": f"Token token={api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._http.close()

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Send a GET request and return parsed JSON.

        Args:
            path: API endpoint path (e.g. ``/incidents``).
            params: Optional query parameters.

        Returns:
            Parsed JSON response body.

        Raises:
            httpx.HTTPStatusError: If the response status indicates an error.
        """
        resp = self._http.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    def put(self, path: str, data: Any = None) -> Any:
        """Send a PUT request with the From header and return parsed JSON.

        Args:
            path: API endpoint path (e.g. ``/incidents/{id}``).
            data: JSON-serializable request body.

        Returns:
            Parsed JSON response body.

        Raises:
            httpx.HTTPStatusError: If the response status indicates an error.
        """
        headers = {}
        if self.email:
            headers["From"] = self.email
        resp = self._http.put(path, json=data, headers=headers)
        resp.raise_for_status()
        return resp.json()
