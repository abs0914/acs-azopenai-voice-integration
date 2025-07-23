#!/bin/bash

echo "🚀 Starting ACS Voice Integration Application..."
echo "📍 Current directory: $(pwd)"
echo "📁 Directory contents: $(ls -la)"

# Set environment variables for Python
export PYTHONPATH="/home/site/wwwroot:$PYTHONPATH"

# Check if we're in the right directory
if [ ! -f "/home/site/wwwroot/main.py" ]; then
    echo "❌ main.py not found in /home/site/wwwroot"
    echo "📁 Contents of /home/site/wwwroot:"
    ls -la /home/site/wwwroot/
    exit 1
fi

# Use the system Python and install packages directly
echo "🐍 Using system Python: $(which python3)"
echo "📦 Installing requirements directly..."

# Install requirements if they exist
if [ -f "/home/site/wwwroot/requirements.txt" ]; then
    echo "📋 Installing requirements..."
    python3 -m pip install --user -r /home/site/wwwroot/requirements.txt
else
    echo "⚠️ No requirements.txt found, skipping package installation"
fi

# Set the port from environment variable or default to 8000
export PORT=${PORT:-8000}

echo "🌐 Starting application on port $PORT..."
echo "🔧 Python path: $PYTHONPATH"

# Try to start the application
cd /home/site/wwwroot
echo "📍 Starting from directory: $(pwd)"
python3 main.py
