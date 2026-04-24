#!/bin/bash
set -e
<<<<<<< HEAD
mkdir -p data/uploads data/logs audio_outputs vector_store_data
echo "Starting StudyMate AI on port ${PORT:-10000}..."
=======

# Create all required directories
mkdir -p data/uploads data/logs audio_outputs vector_store_data

echo "Port: ${PORT}"
echo "Starting uvicorn..."

# Use python -m uvicorn instead of uvicorn binary
# This guarantees the correct Python environment is used
>>>>>>> b74d19266ae8afdd80eefc86391e650c5791343f
python -m uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-10000}"
