#!/bin/bash

# Installation script for Minecraft HTTP Dual Protocol Server
# Run this file to set up the server automatically

echo ""
echo "========================================"
echo "Minecraft HTTP Dual Protocol Server"
echo "Setup Assistant"
echo "========================================"
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python 3.8+ from https://www.python.org"
    exit 1
fi

echo "[OK] Python is installed"
python3 --version

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "To start the server:"
echo "  1. Run: source venv/bin/activate"
echo "  2. Run: python server.py"
echo ""
echo "Then open: http://localhost:12505"
echo ""
echo "To connect in Minecraft:"
echo "  - Server Address: localhost"
echo "  - Server Port: 12505"
echo ""
