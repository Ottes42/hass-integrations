"""Test TimeTagger constants."""
from __future__ import annotations

from custom_components.timetagger.const import (
    DOMAIN,
    CONF_API_URL,
    CONF_TOKEN,
    CONF_WORK_TAGS,
    CONF_DAILY_TARGET,
    DEFAULT_DAILY_TARGET,
    DEFAULT_WORK_TAGS,
    DEFAULT_API_URL,
)


def test_domain() -> None:
    """Test domain constant."""
    assert DOMAIN == "timetagger"


def test_config_constants() -> None:
    """Test configuration constants."""
    assert CONF_API_URL == "api_url"
    assert CONF_TOKEN is None  # Security: no hardcoded token
    assert CONF_WORK_TAGS == "work_tags"
    assert CONF_DAILY_TARGET == "daily_target"


def test_default_values() -> None:
    """Test default configuration values."""
    assert DEFAULT_DAILY_TARGET == 8.0
    assert DEFAULT_WORK_TAGS == "#work,#home"
    assert DEFAULT_API_URL == "https://timetagger-host/timetagger/"


def test_default_types() -> None:
    """Test that defaults have correct types."""
    assert isinstance(DEFAULT_DAILY_TARGET, float)
    assert isinstance(DEFAULT_WORK_TAGS, str)
    assert isinstance(DEFAULT_API_URL, str)