"""Creality Ender-3 V3 integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .coordinator import CrealityEnder3V3Coordinator
from .moonraker import MoonrakerApiAuthRequired, MoonrakerApiClient, MoonrakerApiError

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.CAMERA,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the integration from a config entry."""
    api_key = entry.options.get("api_key", entry.data.get("api_key"))
    client = MoonrakerApiClient(
        hass=hass,
        host=entry.data["host"],
        api_key=api_key,
        base_url=entry.data.get("base_url"),
    )

    try:
        await client.async_initialize()
    except MoonrakerApiAuthRequired as err:
        raise ConfigEntryNotReady("Moonraker API key required") from err
    except MoonrakerApiError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = CrealityEnder3V3Coordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
