#!/bin/bash
set -e
mkdir -p data/uploads data/logs audio_outputs vector_store_data
echo "Starting StudyMate AI on port ${PORT:-10000}..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-10000}"
