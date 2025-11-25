from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import ConfigFlowResult

from .const import (
    DOMAIN,
    CONF_API_URL,
    CONF_TOKEN,
    CONF_WORK_TAGS,
    CONF_DAILY_TARGET,
    DEFAULT_API_URL,
    DEFAULT_WORK_TAGS,
    DEFAULT_DAILY_TARGET,
)


class TimeTaggerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TimeTagger."""

    VERSION = 1

    def is_matching(self, other_flow: config_entries.ConfigFlow) -> bool:
        """Return True if other_flow is matching this flow."""
        if not isinstance(other_flow, TimeTaggerConfigFlow):
            return False
        
        # Compare API URLs to prevent duplicate entries for the same TimeTagger instance
        self_api_url = self.context.get("api_url") or (
            self.init_data.get(CONF_API_URL) if hasattr(self, "init_data") else None
        )
        other_api_url = other_flow.context.get("api_url") or (
            other_flow.init_data.get(CONF_API_URL) if hasattr(other_flow, "init_data") else None
        )
        
        if self_api_url and other_api_url:
            # Normalize URLs by removing trailing slashes for comparison
            self_normalized = self_api_url.rstrip("/").lower()
            other_normalized = other_api_url.rstrip("/").lower()
            return self_normalized == other_normalized
        
        return False

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            api_url = user_input[CONF_API_URL]
            if not api_url.startswith("http"):
                errors["base"] = "invalid_url"
            else:
                return self.async_create_entry(
                    title="TimeTagger",
                    data=user_input,
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_URL, default=DEFAULT_API_URL): str,
                vol.Required(CONF_TOKEN): str,
                vol.Optional(CONF_WORK_TAGS, default=DEFAULT_WORK_TAGS): str,
                vol.Optional(CONF_DAILY_TARGET, default=DEFAULT_DAILY_TARGET): float,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
