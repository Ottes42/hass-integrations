"""Test TimeTagger coordinator."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch
import pytest
from aiohttp import ClientResponseError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.timetagger.coordinator import TimeTaggerCoordinator
from custom_components.timetagger.const import (
    CONF_API_URL,
    CONF_TOKEN,
    CONF_WORK_TAGS,
)


@pytest.fixture
def coordinator_config():
    """Configuration for coordinator tests."""
    return {
        CONF_API_URL: "https://test.timetagger.com/timetagger/",
        CONF_TOKEN: "test_token",
        CONF_WORK_TAGS: "#work,#test",
    }


async def test_coordinator_init(hass: HomeAssistant, coordinator_config) -> None:
    """Test coordinator initialization."""
    coordinator = TimeTaggerCoordinator(hass, coordinator_config)
    
    assert coordinator._api_url == "https://test.timetagger.com/timetagger//api/v2/records"
    assert coordinator._token == "test_token"
    assert coordinator._work_tags == "#work,#test"
    assert coordinator.update_interval == timedelta(minutes=5)


@pytest.mark.parametrize(
    "records,expected_hours",
    [
        ([], 0.0),
        ([{"t1": 1640995200, "t2": 1641024000}], 8.0),  # 8 hours
        ([{"t1": 1640995200, "t2": 1641027600}], 9.0),  # 9 hours
        (
            [
                {"t1": 1640995200, "t2": 1641024000},  # 8 hours
                {"t1": 1641027600, "t2": 1641031200},  # 1 hour
            ],
            9.0,
        ),
    ],
)
async def test_fetch_records_success(
    hass: HomeAssistant,
    coordinator_config,
    mock_aiohttp_session,
    records,
    expected_hours,
) -> None:
    """Test successful fetch of records."""
    coordinator = TimeTaggerCoordinator(hass, coordinator_config)
    
    # Mock the response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"records": records}
    mock_aiohttp_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
    
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end = datetime.now(timezone.utc)
    
    with patch("aiohttp.ClientSession", mock_aiohttp_session):
        result = await coordinator._fetch_records(
            mock_aiohttp_session.return_value.__aenter__.return_value,
            start,
            end,
        )
    
    assert result == records


async def test_fetch_records_api_error(
    hass: HomeAssistant,
    coordinator_config,
    mock_aiohttp_session,
) -> None:
    """Test API error handling."""
    coordinator = TimeTaggerCoordinator(hass, coordinator_config)
    
    # Mock error response
    mock_response = AsyncMock()
    mock_response.status = 401
    mock_response.text.return_value = "Unauthorized"
    mock_aiohttp_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
    
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end = datetime.now(timezone.utc)
    
    with patch("aiohttp.ClientSession", mock_aiohttp_session):
        with pytest.raises(UpdateFailed, match="TimeTagger API error: 401"):
            await coordinator._fetch_records(
                mock_aiohttp_session.return_value.__aenter__.return_value,
                start,
                end,
            )


async def test_async_update_data_success(
    hass: HomeAssistant,
    coordinator_config,
    mock_aiohttp_session,
    mock_timetagger_data,
) -> None:
    """Test successful data update."""
    coordinator = TimeTaggerCoordinator(hass, coordinator_config)
    
    # Mock the response for different time ranges
    mock_response = AsyncMock()
    mock_response.status = 200
    
    def mock_json_side_effect():
        # Return different data based on call order
        if not hasattr(mock_json_side_effect, "call_count"):
            mock_json_side_effect.call_count = 0
        
        mock_json_side_effect.call_count += 1
        
        if mock_json_side_effect.call_count == 1:
            return {"records": mock_timetagger_data["today"]}
        elif mock_json_side_effect.call_count == 2:
            return {"records": mock_timetagger_data["week"]}
        else:
            return {"records": mock_timetagger_data["month"]}
    
    mock_response.json.side_effect = mock_json_side_effect
    mock_aiohttp_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
    
    with patch("aiohttp.ClientSession", mock_aiohttp_session):
        result = await coordinator._async_update_data()
    
    assert "today" in result
    assert "week" in result
    assert "month" in result
    assert result["today"] == mock_timetagger_data["today"]


def test_utc_ts() -> None:
    """Test UTC timestamp conversion."""
    from custom_components.timetagger.coordinator import _utc_ts
    
    # Test with timezone-aware datetime
    dt_with_tz = datetime(2022, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert _utc_ts(dt_with_tz) == 1641038400
    
    # Test with timezone-naive datetime (should be treated as UTC)
    dt_naive = datetime(2022, 1, 1, 12, 0, 0)
    assert _utc_ts(dt_naive) == 1641038400