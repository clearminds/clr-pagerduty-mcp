"""REST client for PagerDuty API v2."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

API_BASE = "https://api.pagerduty.com"


def _raise_with_detail(resp: httpx.Response) -> None:
    """``raise_for_status`` but keep PagerDuty's explanation.

    PagerDuty answers a failed write with a JSON body naming the reason::

        {"error": {"code": 2001, "message": "Invalid Input Provided",
                   "errors": ["Incident Already Resolved"]}}

    Bare ``raise_for_status()`` discards that, so the caller sees only
    "Client error '400 Bad Request'" — which reads as a malformed request and
    sends you looking at your payload. On 2026-08-28 that cost a long detour:
    two ``pd_resolve_incident`` calls returned an unexplained 400 because Zabbix
    had auto-resolved the incidents seconds earlier, and the message that said
    so was being thrown away.

    An error that knows why it failed must say so.
    """
    if not resp.is_error:
        return

    detail = ""
    try:
        payload = resp.json()
    except ValueError:
        payload = None
    if isinstance(payload, dict):
        err = payload.get("error")
        if isinstance(err, dict):
            parts = [str(err.get("message") or "").strip()]
            parts += [str(e).strip() for e in (err.get("errors") or [])]
            detail = ": ".join(p for p in parts if p)
        elif isinstance(err, str):
            detail = err
    if not detail:
        # Some endpoints return an empty body (401 does) — say that rather than
        # nothing, so "no detail" is distinguishable from "never looked".
        detail = resp.text.strip()[:300] or "no error detail in response body"

    raise httpx.HTTPStatusError(
        f"PagerDuty {resp.status_code} for {resp.request.method} {resp.request.url.path}: {detail}",
        request=resp.request,
        response=resp,
    )


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
        _raise_with_detail(resp)
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
        _raise_with_detail(resp)
        return resp.json()
