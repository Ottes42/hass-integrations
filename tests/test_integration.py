"""Integration tests for TimeTagger component."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import entity_registry as er
from homeassistant.const import Platform

from custom_components.timetagger.const import DOMAIN


async def test_full_integration_setup(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_aiohttp_session,
) -> None:
    """Test full integration setup and sensor creation."""
    # Mock successful API responses
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "records": [
            {"t1": 1640995200, "t2": 1641024000},  # 8 hours
            {"t1": 1641027600, "t2": 1641031200},  # 1 hour
        ]
    }
    mock_aiohttp_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
    
    with patch("aiohttp.ClientSession", mock_aiohttp_session):
        # Add the config entry
        mock_config_entry.add_to_hass(hass)
        
        # Set up the integration
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        # Check that the domain is loaded
        assert DOMAIN in hass.data
        
        # Check that the coordinator is created
        assert mock_config_entry.entry_id in hass.data[DOMAIN]
        
        # Check that sensors are created
        entity_registry = er.async_get(hass)
        entities = er.async_entries_for_config_entry(
            entity_registry, mock_config_entry.entry_id
        )
        
        # Should have 5 sensor entities
        assert len(entities) == 5
        
        # Check entity unique IDs
        expected_unique_ids = {
            "timetagger_work_today",
            "timetagger_work_week", 
            "timetagger_work_month",
            "timetagger_remaining_week",
            "timetagger_monthly_balance",
        }
        
        actual_unique_ids = {entity.unique_id for entity in entities}
        assert actual_unique_ids == expected_unique_ids
        
        # Check that all entities are sensor platform
        for entity in entities:
            assert entity.platform == Platform.SENSOR.value


async def test_integration_unload(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_aiohttp_session,
) -> None:
    """Test integration unloading."""
    # First set up the integration
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"records": []}
    mock_aiohttp_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
    
    with patch("aiohttp.ClientSession", mock_aiohttp_session):
        mock_config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        # Verify setup worked
        assert DOMAIN in hass.data
        assert mock_config_entry.entry_id in hass.data[DOMAIN]
        
        # Now unload
        assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        # Verify unload worked
        if DOMAIN in hass.data:
            assert mock_config_entry.entry_id not in hass.data[DOMAIN]


async def test_integration_coordinator_update_failure(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_aiohttp_session,
) -> None:
    """Test integration behavior when coordinator update fails."""
    # Mock API error
    mock_response = AsyncMock()
    mock_response.status = 401
    mock_response.text.return_value = "Unauthorized"
    mock_aiohttp_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
    
    with patch("aiohttp.ClientSession", mock_aiohttp_session):
        mock_config_entry.add_to_hass(hass)
        
        # Setup should fail due to coordinator first refresh failure
        assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
        
        # Domain should still be in data but entry should not be there
        assert mock_config_entry.entry_id not in hass.data.get(DOMAIN, {})