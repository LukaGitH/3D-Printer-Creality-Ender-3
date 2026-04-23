# Changelog

## 0.1.5

- Replaced the raw G-code passthrough with dedicated Home Assistant services for nozzle temperature, bed temperature, and cooldown.

## 0.1.4

- Added a service for sending raw G-code commands to the printer through Moonraker.

## 0.1.3

- Fixed camera entity initialization so Home Assistant can register the camera entity correctly.

## 0.1.2

- Fixed camera handling for Creality setups that expose the webcam through the Moonraker port at `:4408`.
- Made the camera entity use the live stream as the still-image source when snapshot requests are unavailable or unreliable.

## 0.1.1

- Fixed a config flow crash that showed up in Home Assistant as an unexpected error during setup.
- Improved HACS install documentation with clearer step-by-step setup and troubleshooting guidance.
- Fixed camera URL resolution so webcam paths are resolved from the printer host instead of the Moonraker API port.
- Added Moonraker webcam API discovery and fall back to the legacy `/webcam` path when no webcam entry is reported.

## 0.1.0

- Replaced the old OctoPrint split-YAML package with a HACS custom integration.
- Added a config flow that accepts only the printer IP/host.
- Added live read-only entities for printer state, file, progress, nozzle temp, bed temp, and camera.
- Targeted Creality Ender-3 V3 style Moonraker access on `:4408`.
