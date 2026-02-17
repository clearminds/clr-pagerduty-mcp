"""Configuration for PagerDuty MCP Server."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings loaded from environment variables."""

    pagerduty_api_key: str = ""
    pagerduty_email: str = ""  # Required for write ops (From header)
    pagerduty_transport: str = "stdio"
    pagerduty_log_level: str = "INFO"
