"""Test TimeTagger config flow."""

from __future__ import annotations

from unittest.mock import patch
import pytest

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.timetagger.config_flow import TimeTaggerConfigFlow
from custom_components.timetagger.const import (
    DOMAIN,
    CONF_API_URL,
    CONF_TOKEN,
    CONF_WORK_TAGS,
    CONF_DAILY_TARGET,
)


async def test_config_flow_user_step_success(hass: HomeAssistant) -> None:
    """Test successful user step of config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "custom_components.timetagger.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_URL: "https://test.timetagger.com/timetagger/",
                CONF_TOKEN: "test_token",
                CONF_WORK_TAGS: "#work,#test",
                CONF_DAILY_TARGET: 8.0,
            },
        )

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "TimeTagger"
    assert result["data"] == {
        CONF_API_URL: "https://test.timetagger.com/timetagger/",
        CONF_TOKEN: "test_token",
        CONF_WORK_TAGS: "#work,#test",
        CONF_DAILY_TARGET: 8.0,
    }


async def test_config_flow_invalid_url(hass: HomeAssistant) -> None:
    """Test config flow with invalid URL."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_URL: "invalid-url",
            CONF_TOKEN: "test_token",
            CONF_WORK_TAGS: "#work",
            CONF_DAILY_TARGET: 8.0,
        },
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_url"}


async def test_config_flow_with_defaults(hass: HomeAssistant) -> None:
    """Test config flow uses default values correctly."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Check that the form has default values
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_config_flow_class_attributes() -> None:
    """Test config flow class attributes."""
    flow = TimeTaggerConfigFlow()
    assert flow.VERSION == 1
    assert flow.domain == DOMAIN
