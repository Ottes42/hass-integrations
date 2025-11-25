from __future__ import annotations

DOMAIN = "timetagger"

CONF_API_URL = "api_url"
# Do not hardcode secrets; token must be provided via configuration
CONF_TOKEN: str | None = None
CONF_WORK_TAGS = "work_tags"
CONF_DAILY_TARGET = "daily_target"

DEFAULT_DAILY_TARGET = 8.0
DEFAULT_WORK_TAGS = "#work,#home"
DEFAULT_API_URL = "https://timetagger-host/timetagger/"
