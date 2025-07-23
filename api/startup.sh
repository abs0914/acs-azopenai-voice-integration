#!/bin/bash

echo "🚀 Starting ACS Voice Integration Application..."

# Set environment variables for Python
export PYTHONPATH="/home/site/wwwroot:$PYTHONPATH"

# Check if virtual environment exists, if not create it
if [ ! -d "/home/site/wwwroot/antenv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv /home/site/wwwroot/antenv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source /home/site/wwwroot/antenv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements if they exist
if [ -f "/home/site/wwwroot/requirements.txt" ]; then
    echo "📋 Installing requirements..."
    pip install -r /home/site/wwwroot/requirements.txt
else
    echo "⚠️ No requirements.txt found, skipping package installation"
fi

# Set the port from environment variable or default to 8000
export PORT=${PORT:-8000}

echo "🌐 Starting application on port $PORT..."

# Try to start the application
cd /home/site/wwwroot
python main.py
