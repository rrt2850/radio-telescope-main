# Radio Telescope

This repository contains a radio telescope controller with a FastAPI backend and a React + Vite frontend. The backend communicates with an attached Arduino to drive the telescope hardware, while the frontend provides an interface for pointing and tracking targets.

## Repository layout
- `backend/` – FastAPI service for recieving commands and forwarding them to the Arduino. See `backend/README.md` for detailed setup and usage.
- `frontend/` – React UI for interacting with the backend. See `frontend/README.md` for install and run instructions.
- `arduino/` – Arduino files for the telescope controller.
- `start.sh` / `start.ps1` – Helper scripts intended to launch both the backend and frontend together (not reccomended unless you have an arduino connected to your pc)
- `bootstrap.sh` / `bootstrap.ps1` – Scripts to install common prerequisites.

## Prerequisites and hardware
- An Arduino **must** be attached to the machine running the backend for the system to function.
- Python 3.10+ and Node.js (see component READMEs for exact versions and dependencies).
- Access to Cloudflare Tunnel if you plan to expose the backend over the internet.

## Recommended usage
1. The typical deployment is to run the backend on a Raspberry Pi (or similar host) that is physically connected to the Arduino-controlled telescope.
2. Start a Cloudflare tunnel from that device so the API remains reachable from anywhere.
3. Run the frontend locally on your own laptop/desktop and point it at the tunnel URL to command the telescope remotely.

### Running the backend
1. Follow the steps in `backend/README.md` to install Python dependencies.
2. Connect the Arduino to the backend host and verify the serial port path.
3. Launch the API (e.g., `uvicorn main:app --host 0.0.0.0 --port 8000`).
4. Start the Cloudflare tunnel so the backend remains accessible externally.

### Running the frontend
1. Follow the instructions in `frontend/README.md` to install Node dependencies.
2. Start the dev server with `frontend/start.ps1` or `frontend/start.sh`
3. Configure the UI to target the backend URL (local host or Cloudflare tunnel).

## Notes on the combined start scripts
- `start.sh` and `start.ps1` attempt to launch both services together, but they are only useful when the Arduino is connected to your PC.
- For most scenarios, run the backend and frontend independently so each can live where it makes the most sense (e.g., backend on the Pi, frontend on your laptop).

## Remote access
The backend exposes a Cloudflare tunnel so the API can be reached from anywhere. Ensure the tunnel is running on the backend host before attempting to use the frontend remotely. If you don't set up the tunnel, the frontend will still run but none of the requests will succeed