#!/bin/bash
# Installation and verification script for ScoreFinder

set -e

echo "╔══════════════════════════════════════════════╗"
echo "║     ScoreFinder Installation Script          ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "➜ Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
if [ -z "$python_version" ]; then
    echo "✗ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi
echo "✓ Python $python_version found"
echo ""

# Install dependencies
echo "➜ Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Install package in development mode
echo "➜ Installing ScoreFinder..."
pip install -q -e .
echo "✓ ScoreFinder installed"
echo ""

# Check if .env exists
echo "➜ Checking configuration..."
if [ ! -f .env ]; then
    echo "⚠ .env file not found"
    echo "  Creating .env from template..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠ IMPORTANT: Please edit .env and add your API keys:"
    echo "  - GOOGLE_API_KEY"
    echo "  - GOOGLE_SEARCH_ENGINE_ID"
    echo "  - MUSESCORE_PATH (if needed)"
    echo ""
else
    echo "✓ .env file exists"
    echo ""
fi

# Run tests
echo "➜ Running tests..."
if python -m unittest discover tests -v > /dev/null 2>&1; then
    echo "✓ All tests passed"
else
    echo "⚠ Some tests failed (this may be expected without API keys)"
fi
echo ""

# Check configuration
echo "➜ Checking application configuration..."
echo ""
python main.py check
echo ""

echo "╔══════════════════════════════════════════════╗"
echo "║         Installation Complete!               ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Run: python main.py check"
echo "3. Try: python main.py find \"Song Name\" --artist \"Artist\""
echo ""
echo "For more information, see README.md and USAGE.md"
