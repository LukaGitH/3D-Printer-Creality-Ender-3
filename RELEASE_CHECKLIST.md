# Release Checklist

## Before tagging

1. In Home Assistant, add the repository as a HACS custom repository with category `Integration`.
2. Install it from HACS and restart Home Assistant.
3. Add the integration from `Settings -> Devices & Services`.
4. Enter the printer IP only, for example `192.168.0.141`.
5. Verify these entities appear and update live:
   - camera
   - connected
   - printing
   - paused
   - nozzle temperature
   - bed temperature
   - print state
   - file name
   - progress
6. Verify the camera opens and uses `http://<ip>:4408/webcam?action=stream`.
7. If you do not want history, exclude the entities or integration from Home Assistant `recorder`.

## Tagging

1. Commit the release state.
2. Create tag `v0.1.0`.
3. Push branch and tag.
4. Publish a GitHub release for `v0.1.0`.
