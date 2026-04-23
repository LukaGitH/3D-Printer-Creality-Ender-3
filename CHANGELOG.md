# Changelog

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
