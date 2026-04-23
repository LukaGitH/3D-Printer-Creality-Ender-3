"""Moonraker client for Creality printers."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from typing import Any
from urllib.parse import urlencode, urljoin, urlparse

from aiohttp import ClientError, ClientSession

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

LOGGER = logging.getLogger(__name__)

DEFAULT_OBJECTS: dict[str, Sequence[str] | None] = {
    "display_status": ("progress",),
    "extruder": ("temperature", "target"),
    "heater_bed": ("temperature", "target"),
    "print_stats": (
        "filename",
        "state",
    ),
    "webhooks": ("state", "state_message"),
}


class MoonrakerApiError(Exception):
    """Base Moonraker client error."""


class MoonrakerApiAuthRequired(MoonrakerApiError):
    """Raised when the API requires an API key."""


class MoonrakerApiCannotConnect(MoonrakerApiError):
    """Raised when the printer cannot be reached."""


class MoonrakerApiClient:
    """Tiny Moonraker HTTP client."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        api_key: str | None = None,
        base_url: str | None = None,
        session: ClientSession | None = None,
    ) -> None:
        """Initialize the client."""
        self.hass = hass
        self.host = host.strip()
        self.api_key = api_key or None
        self.base_url = (base_url or "").rstrip("/")
        self.normalized_host = self._normalize_host(self.host)
        self.session = session or async_get_clientsession(hass)
        self.logger = LOGGER
        self.available_objects: set[str] = set()
        self.device_unique_id = self.normalized_host

    @property
    def request_headers(self) -> dict[str, str]:
        """Return HTTP headers."""
        if not self.api_key:
            return {}
        return {"X-Api-Key": self.api_key}

    async def async_initialize(self) -> None:
        """Resolve the working base URL and fetch initial metadata."""
        if not self.base_url:
            self.base_url = await self._async_detect_base_url()

        self.available_objects = await self.async_fetch_object_list()
        printer = await self.async_fetch_printer_info()
        self.device_unique_id = (
            printer.get("hostname") or self.normalized_host
        )

    async def async_fetch_data(self) -> dict[str, Any]:
        """Fetch all data needed by entities."""
        server, printer, status, camera = await asyncio.gather(
            self.async_fetch_server_info(),
            self.async_fetch_printer_info(),
            self.async_fetch_status(),
            self.async_fetch_camera_info(),
        )

        print_stats = status.get("print_stats", {})
        display_status = status.get("display_status", {})
        progress = display_status.get("progress")

        return {
            "camera": camera,
            "device": {
                "manufacturer": "Creality",
                "model": "Ender-3 V3 compatible printer",
                "name": printer.get("hostname") or self.normalized_host,
                "sw_version": printer.get("software_version") or server.get("moonraker_version"),
            },
            "print_state": print_stats.get("state", "unknown"),
            "printer": printer,
            "progress": None if progress is None else round(float(progress) * 100, 1),
            "server": server,
            "status": status,
        }

    async def async_fetch_server_info(self) -> dict[str, Any]:
        """Fetch server info."""
        return await self._async_get_json("/server/info")

    async def async_fetch_printer_info(self) -> dict[str, Any]:
        """Fetch printer info."""
        return await self._async_get_json("/printer/info")

    async def async_fetch_system_info(self) -> dict[str, Any]:
        """Fetch machine system info when available."""
        return await self._async_get_json("/machine/system_info")

    async def async_fetch_object_list(self) -> set[str]:
        """Fetch available printer objects."""
        response = await self._async_get_json("/printer/objects/list")
        return set(response.get("objects", []))

    async def async_fetch_camera_info(self) -> dict[str, Any] | None:
        """Fetch configured webcam info, with a legacy fallback."""
        try:
            response = await self._async_get_json("/server/webcams/list")
        except MoonrakerApiError:
            return self._fallback_camera_info()

        webcams = response.get("webcams", [])
        for webcam in webcams:
            if not webcam.get("enabled", True):
                continue

            stream_url = self._resolve_camera_url(webcam.get("stream_url"))
            snapshot_url = self._resolve_camera_url(webcam.get("snapshot_url"))
            if stream_url or snapshot_url:
                return {
                    "name": webcam.get("name") or "Camera",
                    "snapshot_url": snapshot_url,
                    "stream_url": stream_url,
                }

        return self._fallback_camera_info()

    async def async_fetch_status(self) -> dict[str, Any]:
        """Fetch printer object status."""
        query: dict[str, str] = {}
        for obj, fields in DEFAULT_OBJECTS.items():
            if self.available_objects and obj not in self.available_objects:
                continue
            query[obj] = "" if fields is None else ",".join(fields)

        response = await self._async_get_json(
            f"/printer/objects/query?{urlencode(query, doseq=False)}"
        )
        return response.get("status", response)

    async def async_send_gcode(self, script: str | Sequence[str]) -> dict[str, Any]:
        """Send raw G-code to Moonraker."""
        if isinstance(script, str):
            normalized_script = script.strip()
        else:
            normalized_script = "\n".join(line.strip() for line in script if line.strip())

        if not normalized_script:
            raise MoonrakerApiError("G-code command cannot be empty")

        for line in normalized_script.splitlines():
            if line.strip().upper() == "M112":
                raise MoonrakerApiError("Emergency stop command M112 is not allowed")

        return await self._async_post_json(
            "/printer/gcode/script",
            json_payload={"script": normalized_script},
        )

    async def async_set_nozzle_temperature(self, temperature: float) -> dict[str, Any]:
        """Set the nozzle target temperature."""
        return await self.async_send_gcode(f"M104 S{temperature:g}")

    async def async_set_bed_temperature(self, temperature: float) -> dict[str, Any]:
        """Set the bed target temperature."""
        return await self.async_send_gcode(f"M140 S{temperature:g}")

    async def async_cooldown(self) -> dict[str, Any]:
        """Turn off active heater targets."""
        return await self.async_send_gcode(["M104 S0", "M140 S0"])

    async def _async_detect_base_url(self) -> str:
        """Try common Moonraker endpoints until one responds."""
        auth_required = False
        last_error: Exception | None = None

        for base_url in self._candidate_base_urls(self.host):
            try:
                await self._async_get_json("/server/info", base_url=base_url)
            except MoonrakerApiAuthRequired:
                auth_required = True
                last_error = MoonrakerApiAuthRequired()
            except MoonrakerApiError as err:
                last_error = err
            else:
                return base_url.rstrip("/")

        if auth_required and not self.api_key:
            raise MoonrakerApiAuthRequired("Moonraker requires an API key")
        raise MoonrakerApiCannotConnect(
            f"Could not connect to a Moonraker endpoint for {self.normalized_host}"
        ) from last_error

    async def _async_get_json(
        self,
        path: str,
        *,
        base_url: str | None = None,
    ) -> dict[str, Any]:
        """Perform a GET request and return JSON."""
        url = f"{(base_url or self.base_url).rstrip('/')}{path}"
        try:
            async with asyncio.timeout(10):
                async with self.session.get(url, headers=self.request_headers) as response:
                    if response.status in (401, 403):
                        raise MoonrakerApiAuthRequired("Moonraker rejected the request")
                    response.raise_for_status()
                    payload = await response.json()
        except MoonrakerApiAuthRequired:
            raise
        except (TimeoutError, ClientError, ValueError) as err:
            raise MoonrakerApiCannotConnect(str(err)) from err

        if "result" in payload:
            return payload["result"]
        return payload

    async def _async_post_json(
        self,
        path: str,
        *,
        json_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Perform a POST request and return JSON."""
        url = f"{self.base_url.rstrip('/')}{path}"
        try:
            async with asyncio.timeout(10):
                async with self.session.post(
                    url,
                    headers=self.request_headers,
                    json=json_payload,
                ) as response:
                    if response.status in (401, 403):
                        raise MoonrakerApiAuthRequired("Moonraker rejected the request")
                    response.raise_for_status()
                    payload = await response.json()
        except MoonrakerApiAuthRequired:
            raise
        except (TimeoutError, ClientError, ValueError) as err:
            raise MoonrakerApiCannotConnect(str(err)) from err

        if "result" in payload:
            return payload["result"]
        return payload

    def _resolve_camera_url(self, value: str | None) -> str | None:
        """Resolve webcam URLs, preferring the detected Moonraker base URL."""
        if not value:
            return None
        parsed = urlparse(value)
        if parsed.scheme and parsed.netloc:
            return value
        return urljoin(f"{self.base_url}/", value)

    def _fallback_camera_info(self) -> dict[str, Any]:
        """Return a basic legacy webcam config."""
        return {
            "name": "Camera",
            "snapshot_url": urljoin(f"{self.base_url}/", "/webcam?action=snapshot"),
            "stream_url": urljoin(f"{self.base_url}/", "/webcam?action=stream"),
        }

    @staticmethod
    def _normalize_host(host: str) -> str:
        """Normalize the host for identifiers."""
        cleaned = host.strip().rstrip("/")
        if "://" in cleaned:
            cleaned = cleaned.split("://", 1)[1]
        return cleaned.split("/", 1)[0]

    @classmethod
    def _candidate_base_urls(cls, host: str) -> list[str]:
        """Build candidate base URLs from user input."""
        cleaned = host.strip().rstrip("/")
        if "://" in cleaned:
            return [cleaned]

        normalized = cls._normalize_host(cleaned)
        has_explicit_port = ":" in normalized and normalized.count(":") == 1
        if has_explicit_port:
            return [f"http://{normalized}"]

        return [
            f"http://{normalized}:4408",
            f"http://{normalized}:7125",
            f"http://{normalized}",
        ]
