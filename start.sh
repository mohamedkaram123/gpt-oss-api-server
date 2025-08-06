#!/bin/bash

# GPT-OSS API Server Startup Script

echo "🚀 Starting GPT-OSS 120B API Server..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from example..."
    cp .env.example .env
    echo "✏️  Please edit .env file with your configuration before running again."
    exit 1
fi

# Start the server
echo "🌟 Starting server..."
python main.py