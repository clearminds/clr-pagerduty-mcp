"""REST client for PagerDuty API v2."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

API_BASE = "https://api.pagerduty.com"


class PagerDutyClient:
    """PagerDuty REST API v2 client with token auth."""

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
        self._http.close()

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """GET request. Returns parsed JSON."""
        resp = self._http.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    def put(self, path: str, data: Any = None) -> Any:
        """PUT request with From header. Returns parsed JSON."""
        headers = {}
        if self.email:
            headers["From"] = self.email
        resp = self._http.put(path, json=data, headers=headers)
        resp.raise_for_status()
        return resp.json()
