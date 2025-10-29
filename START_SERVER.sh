#!/bin/bash

# DataCore Analytics - Server Startup Script

echo "======================================"
echo "DataCore Analytics - Starting Server"
echo "======================================"
echo ""

# Change to project directory
cd "$(dirname "$0")"

# Run migrations
echo "[1/3] Running database migrations..."
python3 manage.py migrate --run-syncdb

echo ""
echo "[2/3] Checking dependencies..."
python3 -c "import django, pandas, matplotlib, seaborn, sklearn; print('✓ All dependencies installed')"

echo ""
echo "[3/3] Starting development server..."
echo ""
echo "Server will be available at: http://localhost:8000/"
echo "Press CTRL+C to stop the server"
echo ""
echo "======================================"

# Start the server
python3 manage.py runserver 0.0.0.0:8000
