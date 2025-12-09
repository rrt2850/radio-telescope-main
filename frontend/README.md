# Radio Telescope Frontend

A React + Vite interface for sending point or track commands to the Radio Telescope backend. The UI exposes right ascension, declination, and optional tracking duration inputs that POST directly to the API.

## Prerequisites
- Install the current node.js version: https://nodejs.org/en/download

## Getting Started

1. Install dependencies if you haven't run `./bootstrap.ps1` in the parent directory:

   ```bash
   npm install
   ```

2. Start the Vite dev server or run the start file (defaults to port 5173):

   ```bash
   npm run dev
   ```

   ```bash
   ./start.ps1

   or 

   sudo ./start.sh (when I add it later)
   ```

3. Open the URL shown in the terminal (typically http://localhost:5173). The app expects the backend to be reachable at the same origin or via a configured dev proxy.

## Development Notes

- Key dependencies: React 19, Material UI, Axios, and Vite.