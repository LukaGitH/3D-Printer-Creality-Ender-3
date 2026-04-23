"""Binary sensors for Creality Ender-3 V3."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CrealityEnder3V3Coordinator
from .entity import CrealityEnder3V3Entity


@dataclass(frozen=True, kw_only=True)
class CrealityBinarySensorDescription(BinarySensorEntityDescription):
    """Binary sensor description."""

    value_fn: Callable[[dict[str, Any]], bool]


ENTITY_DESCRIPTIONS: tuple[CrealityBinarySensorDescription, ...] = (
    CrealityBinarySensorDescription(
        key="connected",
        translation_key="connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda data: data["printer"].get("state") is not None,
    ),
    CrealityBinarySensorDescription(
        key="printing",
        translation_key="printing",
        icon="mdi:printer-3d-nozzle",
        value_fn=lambda data: data["print_state"] == "printing",
    ),
    CrealityBinarySensorDescription(
        key="paused",
        translation_key="paused",
        icon="mdi:pause-circle",
        value_fn=lambda data: data["print_state"] == "paused",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors."""
    coordinator: CrealityEnder3V3Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        CrealityEnder3V3BinarySensor(coordinator, description)
        for description in ENTITY_DESCRIPTIONS
    )


class CrealityEnder3V3BinarySensor(
    CrealityEnder3V3Entity, CoordinatorEntity[CrealityEnder3V3Coordinator], BinarySensorEntity
):
    """Creality binary sensor."""

    entity_description: CrealityBinarySensorDescription

    def __init__(
        self,
        coordinator: CrealityEnder3V3Coordinator,
        description: CrealityBinarySensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.device_unique_id}_{description.key}"

    @property
    def is_on(self) -> bool:
        """Return the binary sensor state."""
        return self.entity_description.value_fn(self.coordinator.data)
