#!/usr/bin/env bash
# Start the 7X delivery assistant.  http://127.0.0.1:8077
cd "$(dirname "$0")"
exec .venv/bin/python -m uvicorn app.main:app --reload --port "${PORT:-8077}"
