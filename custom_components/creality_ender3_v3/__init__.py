"""Creality Ender-3 V3 integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, SERVICE_SEND_GCODE
from .coordinator import CrealityEnder3V3Coordinator
from .moonraker import MoonrakerApiAuthRequired, MoonrakerApiClient, MoonrakerApiError

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.CAMERA,
    Platform.SENSOR,
]


def _validate_send_gcode_service(data: dict) -> dict:
    """Validate the send G-code service payload."""
    if not data.get("command") and not data.get("commands"):
        raise vol.Invalid("Either command or commands must be provided")
    return data


SEND_GCODE_SERVICE_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required("entity_id"): cv.entity_id,
            vol.Optional("command"): cv.string,
            vol.Optional("commands"): vol.All(cv.ensure_list, [cv.string]),
        },
        extra=vol.PREVENT_EXTRA,
    ),
    _validate_send_gcode_service,
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
    if not hass.services.has_service(DOMAIN, SERVICE_SEND_GCODE):

        async def async_handle_send_gcode(service_call) -> None:
            """Handle the send G-code service."""
            entity_id = service_call.data["entity_id"]
            registry_entry = er.async_get(hass).async_get(entity_id)
            if registry_entry is None or registry_entry.config_entry_id not in hass.data[DOMAIN]:
                raise HomeAssistantError(
                    f"Entity {entity_id} is not managed by the {DOMAIN} integration"
                )

            target_coordinator: CrealityEnder3V3Coordinator = hass.data[DOMAIN][
                registry_entry.config_entry_id
            ]
            script = service_call.data.get("command") or service_call.data["commands"]
            await target_coordinator.async_send_gcode(script)

        hass.services.async_register(
            DOMAIN,
            SERVICE_SEND_GCODE,
            async_handle_send_gcode,
            schema=SEND_GCODE_SERVICE_SCHEMA,
        )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_SEND_GCODE)
    return unload_ok
