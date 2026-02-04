#!/bin/bash
# I put these in their own sh files in case we want to add more stuff that runs at startup
set -e

exec uvicorn main:app --host 0.0.0.0 --port 8000
