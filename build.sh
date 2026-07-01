#!/usr/bin/env bash
set -e

echo "=== Building frontend ==="
cd frontend
npm install
npm run build
cd ..

echo "=== Installing Python dependencies ==="
cd backend
pip install --no-cache-dir -r requirements.txt
cd ..

echo "=== Build complete ==="
