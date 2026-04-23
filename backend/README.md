# Radio Telescope Backend

FastAPI service that converts celestial coordinates into telescope azimuth/altitude commands and forwards them to an attached Arduino controller.

## Prerequisites

- Python 3.10+
- Access to the telescope Arduino over serial (defaults to `/dev/ttyACM0` at 115200 baud)
- Local latitude/longitude/height configured in `constants.py` alongside mechanical limits

## Installation

1. Create and activate a virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Running the API

Start the server on port 8000:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Start the cloudflare tunnel so the frontend can access the backend

```bash
cloudflared tunnel run telescope-api
```

During startup the app attempts to connect to the Arduino and will log a warning if it fails. Shutdown closes the serial connection.

### Available Endpoints

- `POST /point`
  - Body: `{ "ra": float, "dec": float }`
  - Converts RA/Dec to azimuth/altitude using the configured site location and sends a single point command. Rejects requests while tracking or when the target is below/above the allowed elevation limits.

- `POST /track`
  - Body: `{ "ra": float, "dec": float, "duration": int }`
  - Starts background tracking for the given duration (seconds). Returns `409` if tracking is already in progress or `500` if the Arduino is unavailable.

- `GET /stars`
  - Returns star catalog entries from `data.csv`, grouped by approximate distance (derived from parallax) for dropdown-friendly display in the frontend.

### Operational Notes

- Coordinate conversion and elevation bounds are defined in `constants.py` and `robutils.py`.
- Hardware communication flows through `ArduinoController.SendPoint` and the tracking helpers in `tracking.py`.
- The included `start.sh` script (used on the radio telescope host) launches uvicorn in a tmux session and runs a Cloudflare tunnel for remote access. It currently doesn't work and you'll need to run the command on your own :( but we're working on that...

## Development Tips

- Keep the backend and frontend on the same host/port (or configure CORS/proxy) so the UI can reach `/point` and `/track`.
- When testing without hardware, expect serial connection warnings; API calls that require the Arduino will fail until a device is connected.