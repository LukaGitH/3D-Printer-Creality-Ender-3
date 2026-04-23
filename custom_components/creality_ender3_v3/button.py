"""Button entities for Creality Ender-3 V3."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import CrealityEnder3V3Coordinator
from .entity import CrealityEnder3V3Entity


@dataclass(frozen=True, kw_only=True)
class CrealityButtonDescription(ButtonEntityDescription):
    """Button description."""


ENTITY_DESCRIPTIONS: tuple[CrealityButtonDescription, ...] = (
    CrealityButtonDescription(
        key="cooldown",
        translation_key="cooldown",
        icon="mdi:snowflake-thermometer",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities."""
    coordinator: CrealityEnder3V3Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        CrealityEnder3V3Button(coordinator, description) for description in ENTITY_DESCRIPTIONS
    )


class CrealityEnder3V3Button(CrealityEnder3V3Entity, ButtonEntity):
    """Creality action button."""

    entity_description: CrealityButtonDescription

    def __init__(
        self,
        coordinator: CrealityEnder3V3Coordinator,
        description: CrealityButtonDescription,
    ) -> None:
        """Initialize the button entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.device_unique_id}_{description.key}"

    async def async_press(self) -> None:
        """Press the button."""
        await self.coordinator.async_cooldown()
