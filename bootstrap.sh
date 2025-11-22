#!/bin/bash

set -e  # exit on first error

# Colors
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
GREEN='\033[0;32m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

echo -e "\n${CYAN}[1/3] Cleaning old backend environment...${NC}"

# --- Clean backend venv + cache ---
if [ -d "backend/.venv" ]; then
    echo -e "${YELLOW}Removing backend virtual environment...${NC}"
    rm -rf backend/.venv
fi

if [ -d "backend/__pycache__" ]; then
    echo -e "${YELLOW}Removing Python cache...${NC}"
    rm -rf backend/__pycache__
fi

echo -e "\n${CYAN}[2/3] Setting up backend environment...${NC}"

# --- Setup backend ---
cd backend
python3 -m venv .venv
source .venv/bin/activate

echo -e "${YELLOW}Upgrading pip and installing requirements...${NC}"
python -m pip install --upgrade pip
if ! python -m pip install -r requirements.txt; then
    echo -e "${RED}Failed to install Python dependencies.${NC}"
    deactivate
    exit 1
fi

deactivate
cd ..

# --- Setup frontend ---
echo -e "\n${CYAN}[3/3] Setting up frontend environment...${NC}"

if [ -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}Removing old node_modules...${NC}"
    rm -rf frontend/node_modules
fi

if [ -f "frontend/package-lock.json" ]; then
    echo -e "${YELLOW}Removing old package-lock.json...${NC}"
    rm -f frontend/package-lock.json
fi

cd frontend

echo -e "${YELLOW}Installing npm dependencies...${NC}"
if ! npm install; then
    echo -e "${RED}Failed to install frontend dependencies.${NC}"
    exit 1
fi

cd ..

echo -e "\n${GREEN}Setup complete!${NC}"
echo -e "\n${MAGENTA}To start the project, run the start script :)${NC}"
read -p "Press enter to continue..."
