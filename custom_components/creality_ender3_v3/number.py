"""Number entities for Creality Ender-3 V3."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MAX_BED_TEMPERATURE, MAX_NOZZLE_TEMPERATURE
from .coordinator import CrealityEnder3V3Coordinator
from .entity import CrealityEnder3V3Entity


def _status_value(data: dict[str, Any], object_name: str, field: str) -> Any:
    """Read a field from the printer status payload."""
    return data["status"].get(object_name, {}).get(field)


@dataclass(frozen=True, kw_only=True)
class CrealityNumberDescription:
    """Number entity description."""

    key: str
    translation_key: str
    icon: str
    native_min_value: float
    native_max_value: float
    native_step: float
    value_fn: Callable[[dict[str, Any]], float | None]
    set_value_fn: Callable[[CrealityEnder3V3Coordinator, float], Coroutine[Any, Any, None]]


ENTITY_DESCRIPTIONS: tuple[CrealityNumberDescription, ...] = (
    CrealityNumberDescription(
        key="nozzle_target_temperature",
        translation_key="nozzle_target_temperature",
        icon="mdi:printer-3d-nozzle-heat",
        native_min_value=0,
        native_max_value=MAX_NOZZLE_TEMPERATURE,
        native_step=1,
        value_fn=lambda data: _status_value(data, "extruder", "target"),
        set_value_fn=lambda coordinator, value: coordinator.async_set_nozzle_temperature(value),
    ),
    CrealityNumberDescription(
        key="bed_target_temperature",
        translation_key="bed_target_temperature",
        icon="mdi:radiator",
        native_min_value=0,
        native_max_value=MAX_BED_TEMPERATURE,
        native_step=1,
        value_fn=lambda data: _status_value(data, "heater_bed", "target"),
        set_value_fn=lambda coordinator, value: coordinator.async_set_bed_temperature(value),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities."""
    coordinator: CrealityEnder3V3Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        CrealityEnder3V3Number(coordinator, description) for description in ENTITY_DESCRIPTIONS
    )


class CrealityEnder3V3Number(CrealityEnder3V3Entity, NumberEntity):
    """Creality target temperature number."""

    entity_description: CrealityNumberDescription
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: CrealityEnder3V3Coordinator,
        description: CrealityNumberDescription,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.device_unique_id}_{description.key}"
        self._attr_icon = description.icon
        self._attr_native_min_value = description.native_min_value
        self._attr_native_max_value = description.native_max_value
        self._attr_native_step = description.native_step

    @property
    def native_value(self) -> float | None:
        """Return the target temperature."""
        value = self.entity_description.value_fn(self.coordinator.data)
        if value is None:
            return None
        return float(value)

    async def async_set_native_value(self, value: float) -> None:
        """Set the target temperature."""
        await self.entity_description.set_value_fn(self.coordinator, value)
