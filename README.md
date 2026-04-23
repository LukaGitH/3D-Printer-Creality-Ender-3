# Creality Ender-3 V3 for Home Assistant

This repository is now a minimal HACS custom integration instead of a split-YAML OctoPrint package.

It talks directly to a Moonraker-compatible API exposed by the printer and only needs the printer IP or hostname during setup.

## What it adds

- Nozzle and bed temperature sensors
- Print state, current file, and progress
- Printer state binary sensors
- Camera entity from the printer LAN UI
- HACS installable config flow

## Supported connection modes

The integration autodetects common local Moonraker-compatible endpoints for Creality printers:

- `http://<printer-ip>:4408`
- `http://<printer-ip>:7125`
- `http://<printer-ip>`

You can also enter a full URL instead of a bare IP if your printer uses a different port.

## Important note for Ender-3 V3 variants

This integration does not use OctoPrint.

It expects the printer to expose a Moonraker-compatible local API. On some Creality models that is available out of the box, while others need Moonraker enabled first. If your printer does not answer `GET /server/info`, Home Assistant cannot talk to it yet from only the IP.

## HACS install

1. In HACS, add this repository as a custom repository with category `Integration`.
2. Install `Creality Ender-3 V3`.
3. Restart Home Assistant.
4. Go to `Settings -> Devices & Services -> Add Integration`.
5. Select `Creality Ender-3 V3`.
6. Enter the printer IP or hostname.

If your printer requires a Moonraker API key, enter it in the optional field.

## Current scope

This integration is intentionally minimal and read-only:

- monitor printer state
- view temperatures and print progress
- view the LAN camera at `/webcam?action=stream`

Control actions can be added later once the monitoring path is stable across V3 variants.

## No history

If you only want live information in Home Assistant and do not want recorder history, exclude the entities or integration from `recorder`.

```yaml
recorder:
  exclude:
    entity_globs:
      - sensor.ender_3_*
      - binary_sensor.ender_3_*
      - camera.ender_3_*
```

## First release

See [RELEASE_CHECKLIST.md](/home/luka/Projects/Creality/3D-Printer-Creality-Ender-3/RELEASE_CHECKLIST.md) before publishing `v0.1.0`.
