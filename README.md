# pagerduty-mcp-server

PagerDuty incident and on-call management

## Install

```bash
pip install pagerduty-mcp-server
# or
uvx pagerduty-mcp-server
```

## Configuration

**Preferred:** Configuration file at `~/.config/pagerduty/credentials.json` (chmod 600):

```json
{
  "token": "your-api-token",
  "email": "user@example.com"
}
```

Get token: PagerDuty → Configuration → API Access → Create API Key

**Alternative:** Environment variables are also supported:

| Variable | Description | Example |
|----------|-------------|---------|
| `PAGERDUTY_TOKEN` | PagerDuty API token | `your-api-token` |
| `PAGERDUTY_EMAIL` | User email address | `user@example.com` |

See `--help` for additional options:

```bash
pagerduty-mcp-server --help
```

## Development

```bash
git clone https://github.com/clearminds/pagerduty-mcp-server.git
cd pagerduty-mcp-server
uv sync
uv run pagerduty-mcp-server
```

## License

MIT
