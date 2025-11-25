"""Test TimeTagger integration setup."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

from custom_components.timetagger import (
    async_setup_entry,
    async_unload_entry,
    PLATFORMS,
)
from custom_components.timetagger.const import DOMAIN


async def test_async_setup_entry(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_aiohttp_session,
) -> None:
    """Test successful setup of entry."""
    # Mock coordinator methods
    with (
        patch(
            "custom_components.timetagger.TimeTaggerCoordinator.async_config_entry_first_refresh"
        ) as mock_refresh,
        patch(
            "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups"
        ) as mock_forward,
    ):
        mock_refresh.return_value = None
        mock_forward.return_value = True

        result = await async_setup_entry(hass, mock_config_entry)

        assert result is True
        assert DOMAIN in hass.data
        assert mock_config_entry.entry_id in hass.data[DOMAIN]

        # Verify coordinator was created and refreshed
        mock_refresh.assert_called_once()
        mock_forward.assert_called_once_with(mock_config_entry, PLATFORMS)


async def test_async_setup_entry_coordinator_failure(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test setup entry with coordinator failure."""
    with patch(
        "custom_components.timetagger.TimeTaggerCoordinator.async_config_entry_first_refresh"
    ) as mock_refresh:
        mock_refresh.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            await async_setup_entry(hass, mock_config_entry)


async def test_async_unload_entry_success(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test successful unload of entry."""
    # Setup initial data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = AsyncMock()

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms"
    ) as mock_unload:
        mock_unload.return_value = True

        result = await async_unload_entry(hass, mock_config_entry)

        assert result is True
        assert mock_config_entry.entry_id not in hass.data[DOMAIN]
        mock_unload.assert_called_once_with(mock_config_entry, PLATFORMS)


async def test_async_unload_entry_failure(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test unload entry failure."""
    # Setup initial data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = AsyncMock()

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms"
    ) as mock_unload:
        mock_unload.return_value = False

        result = await async_unload_entry(hass, mock_config_entry)

        assert result is False
        # Data should still be there since unload failed
        assert mock_config_entry.entry_id in hass.data[DOMAIN]


async def test_async_unload_entry_no_domain_data(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test unload entry when domain data doesn't exist."""
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms"
    ) as mock_unload:
        mock_unload.return_value = True

        result = await async_unload_entry(hass, mock_config_entry)

        assert result is True
        mock_unload.assert_called_once_with(mock_config_entry, PLATFORMS)


def test_platforms() -> None:
    """Test that platforms are correctly defined."""
    assert PLATFORMS == [Platform.SENSOR]
    assert len(PLATFORMS) == 1
