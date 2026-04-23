# Creality Ender-3 V3 for Home Assistant

This repository is now a minimal HACS custom integration instead of a split-YAML OctoPrint package.

It talks directly to a Moonraker-compatible API exposed by the printer and only needs the printer IP or hostname during setup.

## What it adds

- Nozzle and bed temperature sensors
- Nozzle and bed target temperature controls
- Print state, current file, and progress
- Printer state binary sensors
- Cooldown button entity
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

### Before you start

Make sure:

- HACS is already installed in Home Assistant
- your Home Assistant instance and printer are on the same local network
- you know the printer IP address or local hostname
- the printer answers on at least one of these endpoints:
  - `http://<printer-ip>:4408/server/info`
  - `http://<printer-ip>:7125/server/info`
  - `http://<printer-ip>/server/info`

If you are not sure which IP belongs to the printer, check your router client list or the printer network settings page.

### Add this repository to HACS

1. Open Home Assistant.
2. Go to `HACS -> Integrations`.
3. Open the top-right menu and select `Custom repositories`.
4. Paste this repository URL:

```text
https://github.com/LukaGitH/3D-Printer-Creality-Ender-3
```

5. Set the category to `Integration`.
6. Select `Add`.

After that, the repository should appear in the HACS integrations list.

### Install the integration

1. In `HACS -> Integrations`, search for `Creality Ender-3 V3`.
2. Open the integration page.
3. Select `Download`.
4. Wait for HACS to finish copying the integration files.

### Restart Home Assistant

HACS only places the files in the Home Assistant config directory. Home Assistant still needs a restart before the integration can be discovered.

1. Go to `Settings -> System -> Restart`.
2. Restart Home Assistant.
3. Wait until Home Assistant is fully back online.

If you skip this restart, `Creality Ender-3 V3` may not appear in the integration list.

### Add the integration in Home Assistant

1. Go to `Settings -> Devices & Services`.
2. Select `Add Integration`.
3. Search for `Creality Ender-3 V3`.
4. Enter one of the following:
   - the printer IP, for example `192.168.0.141`
   - the printer hostname, if local DNS works on your network
   - a full URL, if your printer uses a non-default port

Examples:

```text
192.168.0.141
ender3.local
http://192.168.0.141:4408
```

5. Leave the API key field empty unless you know your printer's Moonraker-compatible API requires one.
6. Finish setup and wait for Home Assistant to create the entities.

### What should appear after setup

If the connection succeeds, Home Assistant should create entities such as:

- nozzle temperature
- bed temperature
- print state
- print progress
- current file name
- connected
- printing
- paused
- camera

### If setup fails

Check these points first:

- the printer IP is correct and has not changed
- Home Assistant can reach the printer on your LAN
- the printer exposes a Moonraker-compatible API
- the URL or IP you entered is not blocked by a firewall or VLAN rule
- the printer does not require a port different from `4408`, `7125`, or `80`

Quick browser or API checks from another device on the same network:

```text
http://<printer-ip>:4408/server/info
http://<printer-ip>:7125/server/info
http://<printer-ip>/server/info
```

If none of those endpoints respond, the issue is usually on the printer side or network side rather than in Home Assistant or HACS.

## Current scope

This integration is still intentionally small:

- monitor printer state
- view temperatures and print progress
- control nozzle and bed targets from device entities
- trigger cooldown from a device button entity
- view the LAN camera at `/webcam?action=stream`
- set nozzle temperature, set bed temperature, and cool down through Home Assistant services

### Control temperatures from Home Assistant

Use one of the dedicated services and target any entity created by this integration.

Set nozzle example:

```yaml
service: creality_ender3_v3.set_nozzle_temperature
data:
  entity_id: sensor.ender_3_v3_print_state
  temperature: 200
```

Set bed example:

```yaml
service: creality_ender3_v3.set_bed_temperature
data:
  entity_id: sensor.ender_3_v3_print_state
  temperature: 60
```

Cool down example:

```yaml
service: creality_ender3_v3.cooldown
data:
  entity_id: sensor.ender_3_v3_print_state
```

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
