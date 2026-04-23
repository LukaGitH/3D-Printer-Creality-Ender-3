"""Creality Ender-3 V3 integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    SERVICE_COOLDOWN,
    SERVICE_SET_BED_TEMPERATURE,
    SERVICE_SET_NOZZLE_TEMPERATURE,
)
from .coordinator import CrealityEnder3V3Coordinator
from .moonraker import MoonrakerApiAuthRequired, MoonrakerApiClient, MoonrakerApiError

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CAMERA,
    Platform.NUMBER,
    Platform.SENSOR,
]


TEMPERATURE_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Required("temperature"): vol.All(vol.Coerce(float), vol.Range(min=0, max=300)),
    },
    extra=vol.PREVENT_EXTRA,
)

ENTITY_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
    },
    extra=vol.PREVENT_EXTRA,
)


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
    if not hass.services.has_service(DOMAIN, SERVICE_SET_NOZZLE_TEMPERATURE):

        def _get_target_coordinator(entity_id: str) -> CrealityEnder3V3Coordinator:
            """Resolve the coordinator owning an integration entity."""
            registry_entry = er.async_get(hass).async_get(entity_id)
            if registry_entry is None or registry_entry.config_entry_id not in hass.data[DOMAIN]:
                raise HomeAssistantError(
                    f"Entity {entity_id} is not managed by the {DOMAIN} integration"
                )
            return hass.data[DOMAIN][registry_entry.config_entry_id]

        async def async_handle_set_nozzle_temperature(service_call) -> None:
            """Handle the nozzle temperature service."""
            coordinator = _get_target_coordinator(service_call.data["entity_id"])
            await coordinator.async_set_nozzle_temperature(service_call.data["temperature"])

        async def async_handle_set_bed_temperature(service_call) -> None:
            """Handle the bed temperature service."""
            coordinator = _get_target_coordinator(service_call.data["entity_id"])
            await coordinator.async_set_bed_temperature(service_call.data["temperature"])

        async def async_handle_cooldown(service_call) -> None:
            """Handle the cooldown service."""
            coordinator = _get_target_coordinator(service_call.data["entity_id"])
            await coordinator.async_cooldown()

        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_NOZZLE_TEMPERATURE,
            async_handle_set_nozzle_temperature,
            schema=TEMPERATURE_SERVICE_SCHEMA,
        )
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_BED_TEMPERATURE,
            async_handle_set_bed_temperature,
            schema=TEMPERATURE_SERVICE_SCHEMA,
        )
        hass.services.async_register(
            DOMAIN,
            SERVICE_COOLDOWN,
            async_handle_cooldown,
            schema=ENTITY_SERVICE_SCHEMA,
        )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_SET_NOZZLE_TEMPERATURE)
            hass.services.async_remove(DOMAIN, SERVICE_SET_BED_TEMPERATURE)
            hass.services.async_remove(DOMAIN, SERVICE_COOLDOWN)
    return unload_ok
