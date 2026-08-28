"""Failed API calls must carry PagerDuty's own explanation.

PagerDuty names the reason a write failed in the response body. Bare
``raise_for_status()`` discards it, leaving "Client error '400 Bad Request'" —
which reads as a malformed payload. On 2026-08-28 that turned a one-line answer
("Incident Already Resolved", because Zabbix auto-resolved them seconds earlier)
into a long investigation of the wrong thing.
"""

import httpx
import pytest

from clr_pagerduty_mcp.pd_client import PagerDutyClient


def _client(handler):
    c = PagerDutyClient("tok", "a@b.test")
    c._http = httpx.Client(base_url="https://api.pagerduty.test", transport=httpx.MockTransport(handler))
    return c


class TestErrorDetail:
    def test_put_surfaces_pagerduty_error_message(self):
        """The exact 400 that started it: the body says why, so the exception must."""
        body = {
            "error": {
                "errors": ["Incident Already Resolved"],
                "code": 2001,
                "message": "Invalid Input Provided",
            }
        }
        c = _client(lambda req: httpx.Response(400, json=body))
        with pytest.raises(httpx.HTTPStatusError) as exc:
            c.put("/incidents/PABC123", {"incident": {"status": "resolved"}})
        msg = str(exc.value)
        assert "Incident Already Resolved" in msg
        assert "Invalid Input Provided" in msg
        assert "400" in msg
        c.close()

    def test_get_surfaces_error_message_too(self):
        c = _client(lambda req: httpx.Response(404, json={"error": {"message": "Not Found", "errors": []}}))
        with pytest.raises(httpx.HTTPStatusError, match="Not Found"):
            c.get("/incidents/NOPE")
        c.close()

    def test_empty_body_says_so_rather_than_nothing(self):
        """401 comes back with no body. 'No detail' must be distinguishable from
        'we never looked at the body'."""
        c = _client(lambda req: httpx.Response(401, content=b""))
        with pytest.raises(httpx.HTTPStatusError, match="no error detail in response body"):
            c.get("/incidents")
        c.close()

    def test_non_json_body_is_included_not_swallowed(self):
        c = _client(lambda req: httpx.Response(502, content=b"<html>bad gateway</html>"))
        with pytest.raises(httpx.HTTPStatusError, match="bad gateway"):
            c.get("/incidents")
        c.close()

    def test_string_error_field_is_handled(self):
        """Not every endpoint returns the dict shape."""
        c = _client(lambda req: httpx.Response(403, json={"error": "Access Denied"}))
        with pytest.raises(httpx.HTTPStatusError, match="Access Denied"):
            c.get("/incidents")
        c.close()

    def test_success_is_untouched(self):
        c = _client(lambda req: httpx.Response(200, json={"incident": {"id": "PABC123"}}))
        assert c.get("/incidents/PABC123") == {"incident": {"id": "PABC123"}}
        c.close()

    def test_the_exception_is_still_an_httpstatuserror(self):
        """Callers catch httpx.HTTPStatusError — enriching the message must not
        change the type they handle."""
        c = _client(lambda req: httpx.Response(400, json={"error": {"message": "x", "errors": []}}))
        with pytest.raises(httpx.HTTPStatusError) as exc:
            c.put("/incidents/P1", {})
        assert exc.value.response.status_code == 400
        assert exc.value.request is not None
        c.close()
