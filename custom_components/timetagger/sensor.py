from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_DAILY_TARGET
from .coordinator import TimeTaggerCoordinator


def _sum_hours(records: list[dict[str, Any]]) -> float:
    """Sum t2-t1 in hours over all records."""
    total = 0.0
    for r in records:
        t1 = float(r.get("t1", 0))
        t2 = float(r.get("t2", 0))
        total += max(0, t2 - t1)
    return round(total / 3600.0, 2)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TimeTagger sensors from a config entry."""
    coordinator: TimeTaggerCoordinator = hass.data[DOMAIN][entry.entry_id]
    daily_target = entry.data.get(CONF_DAILY_TARGET, 8.0)

    entities: list[SensorEntity] = [
        TTWorkToday(coordinator, entry),
        TTWorkWeek(coordinator, entry),
        TTWorkMonth(coordinator, entry),
        TTRemainingWeek(coordinator, entry, daily_target),
        TTMonthlyBalance(coordinator, entry, daily_target),
    ]

    async_add_entities(entities)


class TTBaseSensor(CoordinatorEntity[TimeTaggerCoordinator], SensorEntity):
    """Base entity for TimeTagger sensors with common device info."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: TimeTaggerCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry_id = entry.entry_id
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": "TimeTagger",
            "manufacturer": "TimeTagger",
            "model": "API",
        }


class TTWorkToday(TTBaseSensor):
    """Arbeitszeit heute."""

    _attr_name = "Arbeitszeit heute"
    _attr_unique_id = "timetagger_work_today"
    _attr_native_unit_of_measurement = "h"

    @property
    def native_value(self) -> float | None:
        records = self.coordinator.data.get("today", [])
        return _sum_hours(records)


class TTWorkWeek(TTBaseSensor):
    """Arbeitszeit diese Woche."""

    _attr_name = "Arbeitszeit diese Woche"
    _attr_unique_id = "timetagger_work_week"
    _attr_native_unit_of_measurement = "h"

    @property
    def native_value(self) -> float | None:
        records = self.coordinator.data.get("week", [])
        return _sum_hours(records)


class TTWorkMonth(TTBaseSensor):
    """Arbeitszeit diesen Monat."""

    _attr_name = "Arbeitszeit diesen Monat"
    _attr_unique_id = "timetagger_work_month"
    _attr_native_unit_of_measurement = "h"

    @property
    def native_value(self) -> float | None:
        records = self.coordinator.data.get("month", [])
        return _sum_hours(records)


class TTRemainingWeek(TTBaseSensor):
    """Restzeit diese Woche (Soll - Ist)."""

    _attr_name = "Restzeit diese Woche"
    _attr_unique_id = "timetagger_remaining_week"
    _attr_native_unit_of_measurement = "h"

    def __init__(
        self,
        coordinator: TimeTaggerCoordinator,
        entry: ConfigEntry,
        daily_target: float,
    ) -> None:
        super().__init__(coordinator, entry)
        self._daily_target = daily_target

    def _week_target(self) -> float:
        """Simple week target: weekdays passed * daily_target."""
        now = datetime.now()
        weekday = now.weekday()  # 0=Mon
        effective_days = min(weekday + 1, 5)
        return round(effective_days * self._daily_target, 2)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        week_hours = _sum_hours(self.coordinator.data.get("week", []))
        target = self._week_target()
        return {
            "target_hours": target,
            "worked_hours": week_hours,
        }

    @property
    def native_value(self) -> float | None:
        week_hours = _sum_hours(self.coordinator.data.get("week", []))
        target = self._week_target()
        return round(target - week_hours, 2)


class TTMonthlyBalance(TTBaseSensor):
    """Monats-Saldo (Über-/Minusstunden diesen Monat)."""

    _attr_name = "Monats-Saldo Arbeitszeit"
    _attr_unique_id = "timetagger_monthly_balance"
    _attr_native_unit_of_measurement = "h"

    def __init__(
        self,
        coordinator: TimeTaggerCoordinator,
        entry: ConfigEntry,
        daily_target: float,
    ) -> None:
        super().__init__(coordinator, entry)
        self._daily_target = daily_target

    def _monthly_target(self) -> float:
        """Compute target hours for the month up to today (Mon–Fri)."""
        from calendar import monthrange

        now = datetime.now()
        year, month, today = now.year, now.month, now.day
        _, _days_in_month = monthrange(year, month)

        workdays_passed = 0
        for day in range(1, today + 1):
            dt = datetime(year, month, day)
            if dt.weekday() < 5:
                workdays_passed += 1

        return round(workdays_passed * self._daily_target, 2)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        month_hours = _sum_hours(self.coordinator.data.get("month", []))
        target = self._monthly_target()
        return {
            "worked_hours": month_hours,
            "target_hours": target,
        }

    @property
    def native_value(self) -> float | None:
        month_hours = _sum_hours(self.coordinator.data.get("month", []))
        target = self._monthly_target()
        return round(month_hours - target, 2)
