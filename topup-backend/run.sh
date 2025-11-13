#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
