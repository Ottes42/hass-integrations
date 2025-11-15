from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
import logging

import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, CONF_API_URL, CONF_TOKEN, CONF_WORK_TAGS

_LOGGER = logging.getLogger(__name__)


def _utc_ts(dt: datetime) -> int:
    """Return Unix timestamp (int) in UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return int(dt.timestamp())


class TimeTaggerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for TimeTagger API."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        self._hass = hass
        self._api_url: str = config[CONF_API_URL] + "/api/v2/records"
        self._token: str = config[CONF_TOKEN]
        self._work_tags: str = config[CONF_WORK_TAGS]

        super().__init__(
            hass,
            _LOGGER,
            name="TimeTagger Coordinator",
            update_interval=timedelta(minutes=5),
        )

    async def _fetch_records(
        self,
        session: aiohttp.ClientSession,
        start: datetime,
        end: datetime,
    ) -> list[dict[str, Any]]:
        """Fetch records for a given time range."""
        params = {
            "running": "false",
            "hidden": "false",
            "tag": self._work_tags,
            "timerange": f"{_utc_ts(start)}-{_utc_ts(end)}",
        }
        headers = {"authtoken": self._token}

        async with async_timeout.timeout(30):
            async with session.get(self._api_url, params=params, headers=headers) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise UpdateFailed(
                        f"TimeTagger API error: {resp.status} - {body}"
                    )
                data = await resp.json()
                return data.get("records", [])

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from TimeTagger API."""
        now = datetime.now(timezone.utc)

        start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        weekday = now.weekday()  # Monday = 0
        start_week = (now - timedelta(days=weekday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        async with aiohttp.ClientSession() as session:
            today = await self._fetch_records(session, start_today, now)
            week = await self._fetch_records(session, start_week, now)
            month = await self._fetch_records(session, start_month, now)

        return {
            "today": today,
            "week": week,
            "month": month,
        }
