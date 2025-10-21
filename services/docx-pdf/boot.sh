#!/usr/bin/env bash
set -euo pipefail
exec python -m gunicorn app:app -b 0.0.0.0:${PORT:-10000} -k gthread --threads 2 -w 1 -t 600