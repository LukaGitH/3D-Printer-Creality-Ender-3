"""Constants for Creality Ender-3 V3."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "creality_ender3_v3"
CONF_BASE_URL = "base_url"
DEFAULT_SCAN_INTERVAL = timedelta(seconds=5)
SERVICE_SET_NOZZLE_TEMPERATURE = "set_nozzle_temperature"
SERVICE_SET_BED_TEMPERATURE = "set_bed_temperature"
SERVICE_COOLDOWN = "cooldown"
