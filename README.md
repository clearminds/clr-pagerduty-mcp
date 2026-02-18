# clr-pagerduty-mcp

[![PyPI](https://img.shields.io/pypi/v/clr-pagerduty-mcp)](https://pypi.org/project/clr-pagerduty-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

MCP server for PagerDuty — manage incidents, on-call schedules, and services through AI assistants like Claude.

## Features

- **Incident management** — list, view, acknowledge, and resolve incidents
- **On-call visibility** — see who is currently on call across all schedules
- **Service overview** — list all PagerDuty services and their status
- **Schedule management** — list on-call schedules with time zones
- **Escalation policies** — view escalation policies and loop counts
- **Credential file support** — load credentials from `~/.config/pagerduty/credentials.json`
- **Write safety** — write operations require `PAGERDUTY_EMAIL` for attribution via `From` header

## Installation

```bash
pip install clr-pagerduty-mcp
# or
uvx clr-pagerduty-mcp
```

## Configuration

**Preferred:** Configuration file at `~/.config/pagerduty/credentials.json` (chmod 600):

```json
{
  "api_key": "u+your-pagerduty-user-api-key",
  "email": "your-email@company.com"
}
```

Legacy format also supported (`token` instead of `api_key`):

```json
{
  "token": "u+your-pagerduty-user-api-key",
  "email": "your-email@company.com"
}
```

Get API key: PagerDuty → My Profile → User Settings → API Access → Create New API Key

> **Note:** This must be a **User API Token** (starts with `u+`), not a general access key.

**Alternative:** Environment variables are also supported:

| Variable | Description | Example |
|----------|-------------|---------|
| `PAGERDUTY_API_KEY` | PagerDuty User API token | `u+yourtoken` |
| `PAGERDUTY_EMAIL` | User email (required for write ops) | `user@company.com` |

Optional:

| Variable | Description | Default |
|----------|-------------|---------|
| `PAGERDUTY_TRANSPORT` | Transport protocol (`stdio` or `http`) | `stdio` |
| `PAGERDUTY_LOG_LEVEL` | Log level | `INFO` |

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pagerduty": {
      "command": "uvx",
      "args": ["clr-pagerduty-mcp"]
    }
  }
}
```

### Claude Code

Add via CLI:

```bash
claude mcp add pagerduty -- uvx clr-pagerduty-mcp
```

Or add to your `.mcp.json`:

```json
{
  "pagerduty": {
    "command": "uvx",
    "args": ["clr-pagerduty-mcp"]
  }
}
```

### VS Code

Add to your VS Code settings or `.vscode/mcp.json`:

```json
{
  "mcp": {
    "servers": {
      "pagerduty": {
        "command": "uvx",
        "args": ["clr-pagerduty-mcp"]
      }
    }
  }
}
```

**Note:** Configuration is read from `~/.config/pagerduty/credentials.json` or environment variables. No need to specify credentials in MCP config files.

### HTTP Transport

To run as a standalone HTTP server:

```bash
clr-pagerduty-mcp --transport http --host 0.0.0.0 --port 8000
```

## Tools

### Incidents

| Tool | Description | Parameters |
|------|-------------|------------|
| `pd_list_incidents` | List incidents with optional filters | `statuses?`, `urgency?`, `limit?` |
| `pd_get_incident` | Get full detail for a specific incident | `incident_id` |
| `pd_acknowledge_incident` | Acknowledge a triggered incident | `incident_id` |
| `pd_resolve_incident` | Resolve an incident | `incident_id` |

**Incident filter values:**

| Parameter | Accepted values | Default |
|-----------|----------------|---------|
| `statuses` | Comma-separated: `triggered`, `acknowledged`, `resolved` | `triggered,acknowledged` |
| `urgency` | `high`, `low` | all |
| `limit` | 1–100 | 25 |

### On-Call

| Tool | Description |
|------|-------------|
| `pd_list_oncalls` | List who is currently on call across all schedules |

### Services

| Tool | Description |
|------|-------------|
| `pd_list_services` | List all PagerDuty services with status |

### Schedules

| Tool | Description |
|------|-------------|
| `pd_list_schedules` | List all on-call schedules with time zones |

### Escalation Policies

| Tool | Description |
|------|-------------|
| `pd_list_escalation_policies` | List all escalation policies with loop counts |

## Example Usage

Once connected, you can ask your AI assistant things like:

- "Are there any active incidents?"
- "Who is on call right now?"
- "Show me the details for incident PABC123"
- "Acknowledge incident PABC123"
- "Resolve incident PABC123"
- "List all PagerDuty services"
- "What are our on-call schedules?"
- "Show me the escalation policies"

## Safety

All `pd_list_*` and `pd_get_*` tools are **read-only** and safe to call at any time.

`pd_acknowledge_incident` and `pd_resolve_incident` are **write operations** — they change incident status in PagerDuty. These require `PAGERDUTY_EMAIL` to be configured so PagerDuty can attribute the action. Without it, write tools return an error instead of silently failing.

## Technical Notes

- **API:** PagerDuty REST API v2 at `https://api.pagerduty.com`
- **Auth:** Token-based via `Authorization: Token token=<key>` header
- **Write attribution:** PagerDuty requires a `From` email header for PUT requests
- **HTTP client:** httpx with 15-second timeout
- **Transport:** stdio (default) or HTTP via `--transport http`

## Development

```bash
git clone https://github.com/clearminds/clr-pagerduty-mcp.git
cd clr-pagerduty-mcp
uv sync
uv run clr-pagerduty-mcp
```

## License

MIT — see [LICENSE](LICENSE) for details.
