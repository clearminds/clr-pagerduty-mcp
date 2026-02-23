"""Configuration for PagerDuty MCP Server."""

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

CREDS_PATH = Path.home() / ".config" / "pagerduty" / "credentials.json"


class Settings(BaseSettings):
    """Settings loaded from credentials file or environment variables.

    Priority order:
    1. ~/.config/pagerduty/credentials.json
    2. Environment variables (PAGERDUTY_API_KEY, PAGERDUTY_EMAIL) -- override

    Attributes:
        pagerduty_api_key: The PagerDuty REST API token.
        pagerduty_email: Email address required for write operations (From header).
        pagerduty_transport: MCP transport mode (``stdio`` or ``http``).
        pagerduty_log_level: Logging verbosity level.
    """

    pagerduty_api_key: str = ""
    pagerduty_email: str = ""  # Required for write ops (From header)
    pagerduty_transport: str = "stdio"
    pagerduty_log_level: str = "INFO"
    pd_read_only: bool = False

    @field_validator("pd_read_only", mode="before")
    @classmethod
    def _empty_str_to_false(cls, v: Any) -> Any:
        if v == "":
            return False
        return v

    model_config = {"env_prefix": ""}

    def load_credentials(self) -> dict[str, Any]:
        """Load credentials with config-file-first, env-override pattern.

        Returns:
            Dict with api_key and email.
        """
        creds: dict[str, Any] = {}

        # 1. FIRST: Load from environment variables (base/fallback)
        if self.pagerduty_api_key:
            creds["api_key"] = self.pagerduty_api_key
        if self.pagerduty_email:
            creds["email"] = self.pagerduty_email

        # 2. THEN: Override with credentials.json file (takes priority)
        if CREDS_PATH.exists():
            try:
                file_creds: dict[str, Any] = json.loads(CREDS_PATH.read_text())

                if "api_key" in file_creds:
                    creds["api_key"] = file_creds["api_key"]
                elif "token" in file_creds:  # Legacy support
                    creds["api_key"] = file_creds["token"]
                if "email" in file_creds:
                    creds["email"] = file_creds["email"]

                logger.info(f"Loaded PagerDuty credentials from {CREDS_PATH}")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load {CREDS_PATH}: {e}")

        if not (creds.get("api_key") and creds.get("email")):
            logger.warning(
                "No PagerDuty credentials configured. Set PAGERDUTY_API_KEY/PAGERDUTY_EMAIL "
                f"env vars or create {CREDS_PATH}"
            )

        return creds
