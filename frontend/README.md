# Radio Telescope Frontend

A minimal React + Vite interface for sending point or track commands to the Radio Telescope backend. The UI exposes right ascension, declination, and optional tracking duration inputs that POST directly to the API.

## Getting Started

1. Install dependencies:

   ```bash
   npm install
   ```

2. Start the Vite dev server (defaults to port 5173):

   ```bash
   npm run dev
   ```

3. Open the URL shown in the terminal (typically http://localhost:5173). The app expects the backend to be reachable at the same origin or via a configured dev proxy.

## Development Notes

- Key dependencies: React 19, Material UI, Axios, and Vite.
- API calls are made with relative paths (`/point` and `/track`). If your backend runs on a different host/port, update the Axios base URL or add a Vite dev server proxy in `vite.config.js`.
- The main UI lives in `src/components/MapController.tsx`, and `src/App.tsx` simply renders that component.
