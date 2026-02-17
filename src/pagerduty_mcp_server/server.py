"""PagerDuty MCP Server — FastMCP tools for PagerDuty incident management."""

import argparse
import logging
import logging.config
import sys
from typing import Any

from fastmcp import FastMCP

from pagerduty_mcp_server.config import Settings
from pagerduty_mcp_server.pd_client import PagerDutyClient

mcp = FastMCP("PagerDuty")
_client: PagerDutyClient | None = None


# ── Incident tools ───────────────────────────────────────────────────


@mcp.tool
def pd_list_incidents(
    statuses: str | None = None,
    urgency: str | None = None,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """List incidents, optionally filtered by status and urgency.

    Args:
        statuses: Comma-separated statuses to filter — triggered, acknowledged,
                  resolved. Default: triggered,acknowledged (active incidents).
        urgency: Filter by urgency — high or low.
        limit: Max incidents to return (default 25, max 100).

    Returns list of incidents with id, title, status, urgency, service, and timestamps.
    """
    params: dict[str, Any] = {"limit": min(limit, 100)}

    status_list = (statuses or "triggered,acknowledged").split(",")
    for s in status_list:
        params.setdefault("statuses[]", [])
        if isinstance(params["statuses[]"], list):
            params["statuses[]"].append(s.strip())

    if urgency:
        params["urgencies[]"] = [urgency]

    # httpx doesn't natively handle repeated params from lists, build manually
    parts = []
    for k, v in params.items():
        if isinstance(v, list):
            for item in v:
                parts.append((k, item))
        else:
            parts.append((k, v))

    resp = _client._http.get("/incidents", params=parts)
    resp.raise_for_status()
    data = resp.json()

    return [
        {
            "id": inc.get("id"),
            "incident_number": inc.get("incident_number"),
            "title": inc.get("title"),
            "status": inc.get("status"),
            "urgency": inc.get("urgency"),
            "service": inc.get("service", {}).get("summary"),
            "created_at": inc.get("created_at"),
            "last_status_change_at": inc.get("last_status_change_at"),
            "html_url": inc.get("html_url"),
        }
        for inc in data.get("incidents", [])
    ]


@mcp.tool
def pd_get_incident(incident_id: str) -> dict[str, Any]:
    """Get full detail for a specific incident.

    Args:
        incident_id: The PagerDuty incident ID (e.g. "PABC123").

    Returns complete incident information.
    """
    data = _client.get(f"/incidents/{incident_id}")
    return data.get("incident", data)


@mcp.tool
def pd_acknowledge_incident(incident_id: str) -> dict[str, Any]:
    """Acknowledge a triggered incident.

    Requires PAGERDUTY_EMAIL to be configured for the From header.

    Args:
        incident_id: The PagerDuty incident ID to acknowledge.

    Returns updated incident data.
    """
    if not _client.email:
        return {
            "error": "PAGERDUTY_EMAIL not configured — required for write operations"
        }

    data = _client.put(
        f"/incidents/{incident_id}",
        {"incident": {"type": "incident_reference", "status": "acknowledged"}},
    )
    return data.get("incident", data)


@mcp.tool
def pd_resolve_incident(incident_id: str) -> dict[str, Any]:
    """Resolve an incident.

    Requires PAGERDUTY_EMAIL to be configured for the From header.

    Args:
        incident_id: The PagerDuty incident ID to resolve.

    Returns updated incident data.
    """
    if not _client.email:
        return {
            "error": "PAGERDUTY_EMAIL not configured — required for write operations"
        }

    data = _client.put(
        f"/incidents/{incident_id}",
        {"incident": {"type": "incident_reference", "status": "resolved"}},
    )
    return data.get("incident", data)


# ── On-call tools ────────────────────────────────────────────────────


@mcp.tool
def pd_list_oncalls() -> list[dict[str, Any]]:
    """List who is currently on call across all schedules.

    Returns list of on-call entries with user, schedule, start/end times.
    """
    data = _client.get("/oncalls")
    return [
        {
            "user": oc.get("user", {}).get("summary"),
            "schedule": oc.get("schedule", {}).get("summary")
            if oc.get("schedule")
            else None,
            "escalation_policy": oc.get("escalation_policy", {}).get("summary"),
            "escalation_level": oc.get("escalation_level"),
            "start": oc.get("start"),
            "end": oc.get("end"),
        }
        for oc in data.get("oncalls", [])
    ]


# ── Service tools ────────────────────────────────────────────────────


@mcp.tool
def pd_list_services() -> list[dict[str, Any]]:
    """List all PagerDuty services.

    Returns list of services with id, name, status, and description.
    """
    data = _client.get("/services")
    return [
        {
            "id": svc.get("id"),
            "name": svc.get("name"),
            "status": svc.get("status"),
            "description": svc.get("description"),
            "html_url": svc.get("html_url"),
        }
        for svc in data.get("services", [])
    ]


# ── Schedule tools ───────────────────────────────────────────────────


@mcp.tool
def pd_list_schedules() -> list[dict[str, Any]]:
    """List all on-call schedules.

    Returns list of schedules with id, name, time zone.
    """
    data = _client.get("/schedules")
    return [
        {
            "id": sched.get("id"),
            "name": sched.get("name"),
            "time_zone": sched.get("time_zone"),
            "html_url": sched.get("html_url"),
        }
        for sched in data.get("schedules", [])
    ]


# ── Escalation policy tools ─────────────────────────────────────────


@mcp.tool
def pd_list_escalation_policies() -> list[dict[str, Any]]:
    """List all escalation policies.

    Returns list of policies with id, name, number of loops.
    """
    data = _client.get("/escalation_policies")
    return [
        {
            "id": ep.get("id"),
            "name": ep.get("name"),
            "num_loops": ep.get("num_loops"),
            "html_url": ep.get("html_url"),
        }
        for ep in data.get("escalation_policies", [])
    ]


# ── Main entry point ─────────────────────────────────────────────────


def main() -> None:
    """Main entry point for the PagerDuty MCP server."""
    global _client

    settings = Settings()

    parser = argparse.ArgumentParser(description="PagerDuty MCP Server")
    parser.add_argument(
        "--transport", type=str, choices=["stdio", "http"], default=None
    )
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--log-level",
        type=str,
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    parser.add_argument("--pagerduty-api-key", type=str, default=None)
    parser.add_argument("--pagerduty-email", type=str, default=None)
    args = parser.parse_args()

    transport = args.transport or settings.pagerduty_transport
    log_level = args.log_level or settings.pagerduty_log_level
    api_key = args.pagerduty_api_key or settings.pagerduty_api_key
    email = args.pagerduty_email or settings.pagerduty_email

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "console": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "console",
                    "stream": "ext://sys.stderr",
                }
            },
            "root": {"level": log_level, "handlers": ["console"]},
        }
    )

    logger = logging.getLogger(__name__)

    if not api_key:
        logger.error("PAGERDUTY_API_KEY is required")
        sys.exit(1)

    if not email:
        logger.warning("PAGERDUTY_EMAIL not set — write operations will be disabled")

    logger.info("Starting PagerDuty MCP Server")
    _client = PagerDutyClient(api_key, email)

    try:
        if transport == "stdio":
            mcp.run(transport="stdio")
        else:
            mcp.run(transport="http", host=args.host, port=args.port)
    except Exception as e:
        logger.error("Failed to start MCP server: %s", e)
        sys.exit(1)
    finally:
        _client.close()


if __name__ == "__main__":
    main()
