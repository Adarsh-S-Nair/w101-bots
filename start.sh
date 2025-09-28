#!/bin/bash

# Wizard101 Gardening Bot - Start Script
# This script sets up the virtual environment and runs the bot

set -e  # Exit on any error

echo "🌱 Wizard101 Gardening Bot - Starting Setup"
echo "=========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ main.py not found. Please run this script from the project root directory."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "📦 Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
if [ -f "venv/Scripts/activate" ]; then
    # Windows
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
    # Linux/Mac
    source venv/bin/activate
else
    echo "❌ Could not find virtual environment activation script"
    exit 1
fi

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📥 Installing requirements..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Creating .env file from template..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "✅ .env file created from template"
        echo "🔧 Please edit .env file with your Wizard101 credentials before running again"
        echo "   You can edit it with: nano .env"
        exit 0
    else
        echo "❌ env.example not found. Please create .env file manually."
        exit 1
    fi
fi

# Run the bot
echo "🚀 Starting Wizard101 Gardening Bot..."
echo "=========================================="
python main.py

echo "👋 Bot session ended"
