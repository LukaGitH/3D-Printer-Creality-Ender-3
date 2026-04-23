"""Config flow for Creality Ender-3 V3."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_BASE_URL, DOMAIN
from .moonraker import MoonrakerApiAuthRequired, MoonrakerApiClient, MoonrakerApiError


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_API_KEY): str,
    }
)


async def _validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, str]:
    """Validate the user input."""
    client = MoonrakerApiClient(
        hass=hass,
        host=data[CONF_HOST],
        api_key=data.get(CONF_API_KEY),
        session=async_get_clientsession(hass),
    )
    await client.async_initialize()

    printer = await client.async_fetch_printer_info()
    machine = await client.async_fetch_system_info()

    cpu_info = machine.get("cpu_info", {})
    unique_id = (
        cpu_info.get("serial_number")
        or printer.get("hostname")
        or client.normalized_host
    )
    title = printer.get("hostname") or client.normalized_host

    return {
        "title": title,
        "unique_id": unique_id,
        CONF_BASE_URL: client.base_url,
    }


class CrealityEnder3V3ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Creality Ender-3 V3."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await _validate_input(self.hass, user_input)
            except MoonrakerApiAuthRequired:
                errors["base"] = "api_key_required"
            except MoonrakerApiError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info["unique_id"])
                self._abort_if_unique_id_configured(
                    updates={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_API_KEY: user_input.get(CONF_API_KEY),
                        CONF_BASE_URL: info[CONF_BASE_URL],
                    }
                )
                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_API_KEY: user_input.get(CONF_API_KEY),
                        CONF_BASE_URL: info[CONF_BASE_URL],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Create the options flow."""
        return CrealityEnder3V3OptionsFlow(config_entry)


class CrealityEnder3V3OptionsFlow(config_entries.OptionsFlow):
    """Handle integration options."""

    def __init__(self, config_entry) -> None:
        """Initialize the options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage the integration options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_API_KEY,
                        default=self.config_entry.options.get(
                            CONF_API_KEY, self.config_entry.data.get(CONF_API_KEY, "")
                        ),
                    ): str,
                }
            ),
        )
