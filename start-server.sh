#!/bin/bash

# Resume Generator - Local Server Launcher
# This script starts a local web server for testing the application

echo "=================================="
echo "Resume Generator - Server Launcher"
echo "=================================="
echo ""

# Check if Python is available
if command -v python3 &> /dev/null; then
    echo "✓ Python 3 found"
    echo ""
    echo "Starting server on http://localhost:8000"
    echo "Press Ctrl+C to stop the server"
    echo ""
    echo "Open your browser and navigate to:"
    echo "  → http://localhost:8000/QUICKSTART.html (Setup Guide)"
    echo "  → http://localhost:8000/index.html (Login Page)"
    echo ""
    python3 -m http.server 8000
elif command -v python &> /dev/null; then
    echo "✓ Python found"
    echo ""
    echo "Starting server on http://localhost:8000"
    echo "Press Ctrl+C to stop the server"
    echo ""
    echo "Open your browser and navigate to:"
    echo "  → http://localhost:8000/QUICKSTART.html (Setup Guide)"
    echo "  → http://localhost:8000/index.html (Login Page)"
    echo ""
    python -m SimpleHTTPServer 8000
elif command -v php &> /dev/null; then
    echo "✓ PHP found"
    echo ""
    echo "Starting server on http://localhost:8000"
    echo "Press Ctrl+C to stop the server"
    echo ""
    echo "Open your browser and navigate to:"
    echo "  → http://localhost:8000/QUICKSTART.html (Setup Guide)"
    echo "  → http://localhost:8000/index.html (Login Page)"
    echo ""
    php -S localhost:8000
else
    echo "❌ No suitable server found (Python or PHP required)"
    echo ""
    echo "Please install Python or PHP to run this server."
    echo "Alternatively, you can:"
    echo "  1. Install Node.js and run: npx http-server -p 8000"
    echo "  2. Open index.html directly in your browser"
    echo ""
    exit 1
fi
