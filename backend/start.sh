#!/bin/bash
set -e

REPO_DIR="/home/radioastro/radio-telescope-main/backend"

cd "$REPO_DIR"

# Kill existing session if it exists (so reboot doesn't spawn infinite sessions)
if tmux has-session -t telescope 2>/dev/null; then
    tmux kill-session -t telescope
fi

# Start a new tmux session with two windows:
#  - window 1: API (uvicorn)
#  - window 2: Cloudflare tunnel
tmux new-session -d -s telescope -n main "uvicorn main:app --host 0.0.0.0 --port 8000"
tmux split-window -v "cloudflared tunnel run telescope-api"
tmux attach -t telescope

