#!/bin/bash

# Wizard101 Bot - Start Script
# This script sets up the virtual environment and runs the bot

set -e  # Exit on any error

# Parse command line arguments
BOT_TYPE=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --gardening)
            BOT_TYPE="gardening"
            shift
            ;;
        --trivia)
            BOT_TYPE="trivia"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--gardening|--trivia]"
            exit 1
            ;;
    esac
done

echo "🎮 Wizard101 Bot - Starting Setup"
echo "================================="

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

# Show menu if no bot type was specified
if [ -z "$BOT_TYPE" ]; then
    echo ""
    echo "🤖 Select Bot Type:"
    echo "=================="
    echo "1) Gardening Bot"
    echo "2) Trivia Bot"
    echo ""
    read -p "Enter your choice (1-2): " choice
    
    case $choice in
        1)
            BOT_TYPE="gardening"
            ;;
        2)
            BOT_TYPE="trivia"
            ;;
        *)
            echo "❌ Invalid choice. Exiting..."
            exit 1
            ;;
    esac
fi

# Run the bot
echo "🚀 Starting Wizard101 $BOT_TYPE Bot..."
echo "=========================================="
python main.py --type "$BOT_TYPE"

echo "👋 Bot session ended"
