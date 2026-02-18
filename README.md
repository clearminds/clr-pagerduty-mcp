# clr-pagerduty-mcp

PagerDuty incident and on-call management

## Install

```bash
pip install clr-pagerduty-mcp
# or
uvx clr-pagerduty-mcp
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
clr-pagerduty-mcp --help
```

## Development

```bash
git clone https://github.com/clearminds/clr-pagerduty-mcp.git
cd clr-pagerduty-mcp
uv sync
uv run clr-pagerduty-mcp
```

## License

MIT
