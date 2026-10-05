# Combo-Man3

A local controller input visualizer for combo practice and streaming. Live buttons, raw analog axes, directional inputs, and press/release history appear on a configurable frame timeline. A native SDL collector keeps reading input while your game has focus; OBS receives the same data through a local Browser Source.

## Windows quick start

1. Install **Python 3.11 or newer** with the Python launcher (`py`).
2. Download this repository as a ZIP and extract it.
3. Double-click **start.bat**. On first launch it creates a virtual environment and installs dependencies. Keep its console open while using the app.
4. Plug in your controller and open **http://127.0.0.1:8765**. Choose a controller and your game's target FPS.
5. Rename `B0`, `B1`, etc. under Button Labels to match your controller or game. Labels persist per controller GUID in your browser.

No controller yet? Run `start.bat --demo` from a terminal for synthetic inputs.

## OBS overlay

Add a **Browser Source** with URL `http://127.0.0.1:8765/overlay`, width **1100**, height **700**, and FPS **60**. The background is transparent. Keep the collector running. The dashboard's **OBS overlay** link includes your selected device ID and FPS; paste that URL into OBS when using multiple controllers. Device instance IDs can change after unplugging: copy the link again if needed.

OBS has separate browser storage. To use the same labels, open Interact on the source and visit the dashboard temporarily, set labels, then restore the overlay URL. Labels are cosmetic: raw control identifiers remain in exported recordings.

## Features

- USB/Bluetooth devices recognized by SDL/pygame, with hot-plug and multiple-controller selection.
- Raw buttons, analog values, axis direction threshold at ±0.5, and hat directions.
- Independent input collection with a requested 1 ms sampling interval and 60 Hz stream delivery.
- Configurable 1–360 FPS timeline, hold spans, frame gaps, release durations, freeze, clear, and JSON export.
- Last 20,000 transitions retained in memory; latest 30 displayed in history.
- Local-only HTTP server, no cloud service, game injection, or input automation.

## Timing and compatibility limits

**These are observed input frames, not game-engine frames.** Transition timestamps use `time.perf_counter()` and are assigned to frames with `floor(timestamp * selected FPS)`. Collection starts when the server starts. OS scheduling, controller polling, queued hardware reports, and the USB/Bluetooth transport limit precision; the requested 1 ms interval is not guaranteed. Frame rate changes re-project the same timestamps rather than changing recordings. Same-frame press/release transitions can have a duration of zero frames.

SDL compatibility is broad, not universal. Raw button/axis mappings vary; axis 0 is not guaranteed to be a particular stick and trigger rest values can vary. This version exposes raw axes instead of promising standardized trigger mappings. The timeline shows at most 16 lanes. Freeze pauses the view only; capture continues. Clear removes local history only; long-held inputs can appear as an ongoing span with an unknown start until the next press. Browser reconnects recover the collector's bounded history, so history cleared locally may return after reloading.

Game simulation synchronization, saved combo comparison, editable axis mappings/deadzones, controller artwork, and a standalone packaged executable are future work. Hardware behavior on Windows and OBS must be validated with physical controllers.

## Other platforms / development

```sh
python -m venv .venv
# Activate the environment (Windows: .venv\Scripts\activate)
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python server.py
# Hardware-free preview:
python server.py --demo
# Timing/history tests:
python -m unittest discover -s tests
```

Use `--port 8766` to change the port. The server listens only on `127.0.0.1`. Exported JSON contains raw controls, down/up states, elapsed seconds, sequence IDs, selected FPS and labels. Dependencies: pygame (SDL) and aiohttp.
