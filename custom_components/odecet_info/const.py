"""Constants for the Odecet.info integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "odecet_info"
PLATFORMS: Final = [Platform.SENSOR, Platform.BUTTON]

CONF_USERNAME: Final = "username"
CONF_PASSWORD: Final = "password"
CONF_SIGNIN_URL: Final = "signin_url"
CONF_MEDIUMS: Final = "mediums"
CONF_FETCH_METHOD: Final = "fetch_method"
CONF_SYNC_FROM: Final = "sync_from"

DEFAULT_SIGNIN_URL: Final = "https://odecet.info/signin"
MIN_SYNC_INTERVAL: Final = timedelta(seconds=60)
DAILY_HOUR: Final = 4
DAILY_JITTER: Final = timedelta(minutes=30)
MAX_FAILURES: Final = 5
BACKOFF_CAP: Final = timedelta(hours=6)
