from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

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

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
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
