# pagerduty-mcp-server

PagerDuty incident and on-call management

## Install

```bash
pip install pagerduty-mcp-server
# or
uvx pagerduty-mcp-server
```

## Configuration

Configuration via environment variables. See `--help` for all options:

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
