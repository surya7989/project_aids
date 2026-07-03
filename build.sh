#!/usr/bin/env bash
set -e

echo "=== Installing Python dependencies ==="
pip install --no-cache-dir -r requirements.txt

echo "=== Build complete ==="
