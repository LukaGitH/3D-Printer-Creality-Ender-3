"""Sensors for Creality Ender-3 V3."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CrealityEnder3V3Coordinator
from .entity import CrealityEnder3V3Entity


def _status_value(data: dict[str, Any], object_name: str, field: str) -> Any:
    """Read a field from the printer status payload."""
    return data["status"].get(object_name, {}).get(field)


def _print_info_value(data: dict[str, Any], field: str) -> Any:
    """Read a field from print_stats.info."""
    return data["status"].get("print_stats", {}).get("info", {}).get(field)


@dataclass(frozen=True, kw_only=True)
class CrealitySensorDescription(SensorEntityDescription):
    """Sensor description."""

    value_fn: Callable[[dict[str, Any]], Any]


ENTITY_DESCRIPTIONS: tuple[CrealitySensorDescription, ...] = (
    CrealitySensorDescription(
        key="nozzle_temperature",
        translation_key="nozzle_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _status_value(data, "extruder", "temperature"),
    ),
    CrealitySensorDescription(
        key="bed_temperature",
        translation_key="bed_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _status_value(data, "heater_bed", "temperature"),
    ),
    CrealitySensorDescription(
        key="progress",
        translation_key="progress",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["progress"],
    ),
    CrealitySensorDescription(
        key="print_state",
        translation_key="print_state",
        icon="mdi:printer-3d",
        value_fn=lambda data: data["print_state"],
    ),
    CrealitySensorDescription(
        key="file_name",
        translation_key="file_name",
        icon="mdi:file",
        value_fn=lambda data: _status_value(data, "print_stats", "filename"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator: CrealityEnder3V3Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        CrealityEnder3V3Sensor(coordinator, description)
        for description in ENTITY_DESCRIPTIONS
    )


class CrealityEnder3V3Sensor(
    CrealityEnder3V3Entity, CoordinatorEntity[CrealityEnder3V3Coordinator], SensorEntity
):
    """Creality sensor."""

    entity_description: CrealitySensorDescription

    def __init__(
        self,
        coordinator: CrealityEnder3V3Coordinator,
        description: CrealitySensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.device_unique_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return the entity state."""
        return self.entity_description.value_fn(self.coordinator.data)
