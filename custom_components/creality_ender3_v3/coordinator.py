"""Data coordinator for Creality Ender-3 V3."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL
from .moonraker import MoonrakerApiClient, MoonrakerApiError


class CrealityEnder3V3Coordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate printer updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: MoonrakerApiClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger=client.logger,
            name=entry.title,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.entry = entry
        self.client = client
        self.device_unique_id = client.device_unique_id

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the printer."""
        try:
            return await self.client.async_fetch_data()
        except MoonrakerApiError as err:
            raise UpdateFailed(str(err)) from err

    async def async_send_gcode(self, script: str | list[str]) -> None:
        """Send G-code and refresh state."""
        try:
            await self.client.async_send_gcode(script)
        except MoonrakerApiError as err:
            raise UpdateFailed(str(err)) from err

        await self.async_refresh()
