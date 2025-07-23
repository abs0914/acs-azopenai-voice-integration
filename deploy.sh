#!/bin/bash

# Azure App Service deployment script
echo "Starting deployment..."

# Install dependencies
echo "Installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "Deployment completed successfully!"
