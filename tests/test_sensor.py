"""Test TimeTagger sensors."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.timetagger.sensor import (
    async_setup_entry,
    _sum_hours,
    TTWorkToday,
    TTWorkWeek,
    TTWorkMonth,
    TTRemainingWeek,
    TTMonthlyBalance,
)
from custom_components.timetagger.const import DOMAIN


async def test_async_setup_entry(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_coordinator,
) -> None:
    """Test sensor setup entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator

    entities = []

    def mock_add_entities(new_entities):
        entities.extend(new_entities)

    await async_setup_entry(hass, mock_config_entry, mock_add_entities)

    assert len(entities) == 5
    assert isinstance(entities[0], TTWorkToday)
    assert isinstance(entities[1], TTWorkWeek)
    assert isinstance(entities[2], TTWorkMonth)
    assert isinstance(entities[3], TTRemainingWeek)
    assert isinstance(entities[4], TTMonthlyBalance)


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
        ([{"t1": 1641031200, "t2": 1640995200}], 0.0),  # Negative time (should be 0)
        ([{"t1": 0, "t2": 0}], 0.0),  # Zero time
        ([{"t1": None, "t2": 1641024000}], 8.0),  # Missing t1
        ([{"t1": 1640995200, "t2": None}], 0.0),  # Missing t2
    ],
)
def test_sum_hours(records, expected_hours) -> None:
    """Test _sum_hours function."""
    result = _sum_hours(records)
    assert result == expected_hours


class TestTTWorkToday:
    """Test TTWorkToday sensor."""

    def test_attributes(self, mock_coordinator, mock_config_entry) -> None:
        """Test sensor attributes."""
        sensor = TTWorkToday(mock_coordinator, mock_config_entry)

        assert sensor._attr_name == "Working hours today"
        assert sensor._attr_unique_id == "timetagger_work_today"
        assert sensor._attr_native_unit_of_measurement == "h"
        assert sensor._attr_has_entity_name is True

    def test_native_value(self, mock_coordinator, mock_config_entry) -> None:
        """Test native value calculation."""
        sensor = TTWorkToday(mock_coordinator, mock_config_entry)

        # Test with mock data (2 records: 8h + 1h = 9h)
        assert sensor.native_value == 9.0

    def test_device_info(self, mock_coordinator, mock_config_entry) -> None:
        """Test device info."""
        sensor = TTWorkToday(mock_coordinator, mock_config_entry)

        device_info = sensor._attr_device_info
        assert device_info["identifiers"] == {(DOMAIN, mock_config_entry.entry_id)}
        assert device_info["name"] == "TimeTagger"
        assert device_info["manufacturer"] == "TimeTagger"
        assert device_info["model"] == "API"


class TestTTWorkWeek:
    """Test TTWorkWeek sensor."""

    def test_attributes(self, mock_coordinator, mock_config_entry) -> None:
        """Test sensor attributes."""
        sensor = TTWorkWeek(mock_coordinator, mock_config_entry)

        assert sensor._attr_name == "Working hours this week"
        assert sensor._attr_unique_id == "timetagger_work_week"
        assert sensor._attr_native_unit_of_measurement == "h"

    def test_native_value(self, mock_coordinator, mock_config_entry) -> None:
        """Test native value calculation."""
        sensor = TTWorkWeek(mock_coordinator, mock_config_entry)

        # Test with mock data (3 records: 8h + 1h + 8h = 17h)
        assert sensor.native_value == 17.0


class TestTTWorkMonth:
    """Test TTWorkMonth sensor."""

    def test_attributes(self, mock_coordinator, mock_config_entry) -> None:
        """Test sensor attributes."""
        sensor = TTWorkMonth(mock_coordinator, mock_config_entry)

        assert sensor._attr_name == "Working hours this month"
        assert sensor._attr_unique_id == "timetagger_work_month"
        assert sensor._attr_native_unit_of_measurement == "h"

    def test_native_value(self, mock_coordinator, mock_config_entry) -> None:
        """Test native value calculation."""
        sensor = TTWorkMonth(mock_coordinator, mock_config_entry)

        # Test with mock data (4 records: 8h + 1h + 8h + 8h = 25h)
        assert sensor.native_value == 25.0


class TestTTRemainingWeek:
    """Test TTRemainingWeek sensor."""

    def test_attributes(self, mock_coordinator, mock_config_entry) -> None:
        """Test sensor attributes."""
        sensor = TTRemainingWeek(mock_coordinator, mock_config_entry, 8.0)

        assert sensor._attr_name == "Remaining time this week"
        assert sensor._attr_unique_id == "timetagger_remaining_week"
        assert sensor._attr_native_unit_of_measurement == "h"
        assert sensor._daily_target == 8.0

    @patch("custom_components.timetagger.sensor.datetime")
    def test_week_target(
        self, mock_datetime, mock_coordinator, mock_config_entry
    ) -> None:
        """Test week target calculation."""
        # Mock Monday (weekday = 0)
        mock_datetime.now.return_value.weekday.return_value = 0

        sensor = TTRemainingWeek(mock_coordinator, mock_config_entry, 8.0)
        assert sensor._week_target() == 8.0  # 1 day * 8 hours

        # Mock Friday (weekday = 4)
        mock_datetime.now.return_value.weekday.return_value = 4
        assert sensor._week_target() == 40.0  # 5 days * 8 hours

        # Mock Saturday (weekday = 5) - should still be 5 days max
        mock_datetime.now.return_value.weekday.return_value = 5
        assert sensor._week_target() == 40.0  # 5 days * 8 hours (capped)

    @patch("custom_components.timetagger.sensor.datetime")
    def test_native_value(
        self, mock_datetime, mock_coordinator, mock_config_entry
    ) -> None:
        """Test native value calculation."""
        # Mock Wednesday (weekday = 2)
        mock_datetime.now.return_value.weekday.return_value = 2

        sensor = TTRemainingWeek(mock_coordinator, mock_config_entry, 8.0)

        # Target: 3 days * 8 hours = 24h
        # Worked: 17h (from mock data)
        # Remaining: 24h - 17h = 7h
        assert sensor.native_value == 7.0

    @patch("custom_components.timetagger.sensor.datetime")
    def test_extra_state_attributes(
        self, mock_datetime, mock_coordinator, mock_config_entry
    ) -> None:
        """Test extra state attributes."""
        mock_datetime.now.return_value.weekday.return_value = 2

        sensor = TTRemainingWeek(mock_coordinator, mock_config_entry, 8.0)
        attributes = sensor.extra_state_attributes

        assert attributes["target_hours"] == 24.0
        assert attributes["worked_hours"] == 17.0


class TestTTMonthlyBalance:
    """Test TTMonthlyBalance sensor."""

    def test_attributes(self, mock_coordinator, mock_config_entry) -> None:
        """Test sensor attributes."""
        sensor = TTMonthlyBalance(mock_coordinator, mock_config_entry, 8.0)

        assert sensor._attr_name == "Monthly working time balance"
        assert sensor._attr_unique_id == "timetagger_monthly_balance"
        assert sensor._attr_native_unit_of_measurement == "h"
        assert sensor._daily_target == 8.0

    @patch("custom_components.timetagger.sensor.datetime")
    def test_monthly_target(
        self, mock_datetime, mock_coordinator, mock_config_entry
    ) -> None:
        """Test monthly target calculation."""
        # Mock January 15th, 2022 (Saturday)
        mock_datetime.now.return_value = datetime(2022, 1, 15)
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        sensor = TTMonthlyBalance(mock_coordinator, mock_config_entry, 8.0)

        # Calculate expected workdays from Jan 1-15, 2022
        # 1-2: Weekend, 3-7: 5 weekdays, 8-9: Weekend, 10-14: 5 weekdays, 15: Saturday
        # Total weekdays: 10
        expected_target = 10 * 8.0  # 80 hours

        assert sensor._monthly_target() == expected_target

    @patch("custom_components.timetagger.sensor.datetime")
    def test_native_value(
        self, mock_datetime, mock_coordinator, mock_config_entry
    ) -> None:
        """Test native value calculation."""
        # Mock a date where monthly target would be 80 hours
        mock_datetime.now.return_value = datetime(2022, 1, 15)
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        sensor = TTMonthlyBalance(mock_coordinator, mock_config_entry, 8.0)

        # Worked: 25h (from mock data)
        # Target: 80h (10 weekdays * 8h)
        # Balance: 25h - 80h = -55h (negative)
        assert sensor.native_value == -55.0

    @patch("custom_components.timetagger.sensor.datetime")
    def test_extra_state_attributes(
        self, mock_datetime, mock_coordinator, mock_config_entry
    ) -> None:
        """Test extra state attributes."""
        mock_datetime.now.return_value = datetime(2022, 1, 15)
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        sensor = TTMonthlyBalance(mock_coordinator, mock_config_entry, 8.0)
        attributes = sensor.extra_state_attributes

        assert attributes["worked_hours"] == 25.0
        assert attributes["target_hours"] == 80.0
