"""Camera platform for Creality Ender-3 V3."""

from __future__ import annotations

from aiohttp import ClientError

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CrealityEnder3V3Coordinator
from .entity import CrealityEnder3V3Entity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the camera platform."""
    coordinator: CrealityEnder3V3Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CrealityEnder3V3Camera(coordinator)])


class CrealityEnder3V3Camera(
    CrealityEnder3V3Entity, CoordinatorEntity[CrealityEnder3V3Coordinator], Camera
):
    """Camera entity backed by Moonraker webcam data."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CrealityEnder3V3Coordinator) -> None:
        """Initialize the camera."""
        super().__init__(coordinator)
        self._attr_name = "Camera"
        self._attr_unique_id = f"{coordinator.device_unique_id}_camera"
        self._attr_brand = "Creality"
        self._attr_is_streaming = True

    @property
    def available(self) -> bool:
        """Return availability."""
        return super().available and self.coordinator.data["camera"] is not None

    @property
    def supported_features(self) -> CameraEntityFeature:
        """Return camera features."""
        if self.coordinator.data["camera"] and self.coordinator.data["camera"].get("stream_url"):
            return CameraEntityFeature.STREAM
        return CameraEntityFeature(0)

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a still image."""
        del width, height
        camera = self.coordinator.data["camera"]
        if not camera or not camera.get("snapshot_url"):
            return None

        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                camera["snapshot_url"],
                headers=self.coordinator.client.request_headers,
            ) as response:
                response.raise_for_status()
                return await response.read()
        except ClientError:
            return None

    async def stream_source(self) -> str | None:
        """Return the stream source."""
        camera = self.coordinator.data["camera"]
        if not camera:
            return None
        return camera.get("stream_url")
