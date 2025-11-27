#!/bin/bash

# AutoHedge Local Startup Script
# This script helps you run AutoHedge locally with ease

echo "🚀 AutoHedge - Starting Local Setup"
echo "===================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your OPENAI_API_KEY"
    echo "You can get an API key from: https://platform.openai.com/api-keys"
    echo ""
    read -p "Press Enter after you've added your API key to .env..."
fi

# Check if OpenAI API key is set
if grep -q "your_openai_api_key_here" .env; then
    echo "❌ Error: Please set your OPENAI_API_KEY in .env file"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip first."
    exit 1
fi

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"

# Create necessary directories
mkdir -p outputs
mkdir -p logs
mkdir -p agent_workspace

echo "✅ Created output directories"

# Start the API server in the background
echo ""
echo "🔥 Starting AutoHedge API server..."
echo "API will be available at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""

# Export environment variables
export $(grep -v '^#' .env | xargs)

# Start the API
python3 api/api.py &
API_PID=$!

echo "API Server PID: $API_PID"

# Wait for API to start
echo "Waiting for API to start..."
sleep 5

# Check if API is running
if ! ps -p $API_PID > /dev/null; then
    echo "❌ API server failed to start"
    exit 1
fi

echo "✅ API server is running!"
echo ""
echo "🌐 Opening Web Interface..."
echo "========================================="
echo "Web UI: file://$(pwd)/web_ui.html"
echo ""
echo "To stop the server, run: kill $API_PID"
echo "Or use: pkill -f 'python3 api/api.py'"
echo ""
echo "📊 Ready to analyze stocks!"
echo "========================================="

# Open the web UI in default browser (if available)
if command -v xdg-open &> /dev/null; then
    xdg-open web_ui.html
elif command -v open &> /dev/null; then
    open web_ui.html
else
    echo "Please open web_ui.html in your browser manually"
fi

# Keep script running and show logs
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
tail -f logs/autohedge_*.log 2>/dev/null || echo "Waiting for logs..."

# Cleanup on exit
trap "kill $API_PID 2>/dev/null" EXIT
