"""Common fixtures for TimeTagger tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.timetagger.const import (
    DOMAIN,
    CONF_API_URL,
    CONF_TOKEN,
    CONF_WORK_TAGS,
    CONF_DAILY_TARGET,
)


@pytest.fixture
def mock_config_entry() -> ConfigEntry:
    """Create a mock config entry."""
    return ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="TimeTagger",
        data={
            CONF_API_URL: "https://test.timetagger.com/timetagger/",
            CONF_TOKEN: "test_token_123",
            CONF_WORK_TAGS: "#work,#test",
            CONF_DAILY_TARGET: 8.0,
        },
        source="user",
        entry_id="test_entry_id",
    )


@pytest.fixture
def mock_timetagger_data():
    """Mock TimeTagger API response data."""
    return {
        "today": [
            {"t1": 1640995200, "t2": 1641024000},  # 8 hours
            {"t1": 1641027600, "t2": 1641031200},  # 1 hour
        ],
        "week": [
            {"t1": 1640995200, "t2": 1641024000},  # 8 hours
            {"t1": 1641027600, "t2": 1641031200},  # 1 hour
            {"t1": 1640908800, "t2": 1640937600},  # 8 hours (previous day)
        ],
        "month": [
            {"t1": 1640995200, "t2": 1641024000},  # 8 hours
            {"t1": 1641027600, "t2": 1641031200},  # 1 hour
            {"t1": 1640908800, "t2": 1640937600},  # 8 hours
            {"t1": 1640822400, "t2": 1640851200},  # 8 hours (2 days ago)
        ],
    }


@pytest.fixture
def mock_coordinator(mock_timetagger_data):
    """Create a mock coordinator."""
    coordinator = AsyncMock()
    coordinator.data = mock_timetagger_data
    coordinator.last_update_success = True
    return coordinator


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp ClientSession."""
    with patch("aiohttp.ClientSession") as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "records": [
                {"t1": 1640995200, "t2": 1641024000},
                {"t1": 1641027600, "t2": 1641031200},
            ]
        }
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        yield mock_session
