#!/bin/bash
# Start the backend FastAPI server

# Activate virtual environment
source .venv/bin/activate

# Start uvicorn server
uvicorn app.main:app --reload
