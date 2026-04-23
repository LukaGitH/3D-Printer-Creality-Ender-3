"""Shared entity helpers."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CrealityEnder3V3Coordinator


class CrealityEnder3V3Entity(CoordinatorEntity[CrealityEnder3V3Coordinator]):
    """Base entity for the integration."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CrealityEnder3V3Coordinator) -> None:
        """Initialize the base entity."""
        super().__init__(coordinator)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device metadata."""
        data = self.coordinator.data
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.device_unique_id)},
            name=data["device"]["name"],
            manufacturer=data["device"]["manufacturer"],
            model=data["device"]["model"],
            sw_version=data["device"]["sw_version"],
            configuration_url=self.coordinator.client.base_url,
        )
