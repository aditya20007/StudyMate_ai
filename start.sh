#!/bin/bash
set -e

# Create all required directories
mkdir -p data/uploads data/logs audio_outputs vector_store_data

echo "Port: ${PORT}"
echo "Starting uvicorn..."

# Use python -m uvicorn instead of uvicorn binary
# This guarantees the correct Python environment is used
python -m uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-10000}"
