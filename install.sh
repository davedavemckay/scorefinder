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

# Set SFHOME environment variable
if [ -z "$SFHOME" ]; then
    export SFHOME=$PWD
    echo "➜ Setting SFHOME to $SFHOME"
    echo "✓ SFHOME set"
    echo ""
else
    echo "➜ SFHOME is already set to $SFHOME"
    echo ""
fi

# Add SFHOME to .bashrc if not already present
echo "Would you like to add SFHOME to your ~/.bashrc for future sessions? (y/n)"
read -r add_sfhome
if [[ "$add_sfhome" =~ ^[Yy]$ ]]; then
    if ! grep -q 'export SFHOME=' ~/.bashrc; then
        echo "➜ Adding SFHOME to ~/.bashrc..."
        echo "export SFHOME=\"$SFHOME\"" >> ~/.bashrc
        echo "✓ SFHOME added to ~/.bashrc"
        echo ""
    else
        echo "➜ SFHOME already present in ~/.bashrc"
        echo ""
    fi
fi

# Add bin dir to PATH environment variable
if [ `echo $PATH | grep -c $SFHOME/bin` -eq 0 ]; then
    export PATH=$SFHOME/bin:$PATH
fi

# Add bin dir to PATH in .bashrc if not already present
echo "Would you like to add SFHOME/bin to your PATH environment variable via ~/.bashrc for future sessions? (y/n)"
read -r add_bin
if [[ "$add_bin" =~ ^[Yy]$ ]]; then
    if ! grep -q $SFHOME/bin ~/.bashrc; then
        echo "➜ Adding SFHOME/bin to PATH via ~/.bashrc..."
        echo "export PATH=\"$SFHOME/bin:\$PATH\"" >> ~/.bashrc
        echo "✓ SFHOME/bin added to ~/.bashrc"
        echo ""
    else
        echo "➜ SFHOME/bin already present in ~/.bashrc"
        echo ""
    fi
fi

# Check if .scorefinder exists
echo "➜ Checking configuration..."
if [ ! -f ~/.scorefinder ]; then
    echo "⚠ ~/.scorefinder file not found"
    echo "  Creating .scorefinder from template..."
    cp .scorefinder.example ~/.scorefinder
    echo "✓ Created ~/.scorefinder file"
    echo ""
    echo "⚠ IMPORTANT: Please edit ~/.scorefinder and add your API keys:"
    echo "  - GOOGLE_API_KEY"
    echo "  - GOOGLE_SEARCH_ENGINE_ID"
    echo "  - MUSESCORE_PATH (if needed)"
    echo ""
else
    echo "✓ ~/.scorefinder file exists"
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
echo "1. Run: python main.py check"
echo "2. Run: scorefinder.sh from any folder"
echo "3. Try: scorefinder.sh find \"Song Name\" --artist \"Artist\""
echo ""
echo "For more information, see README.md and USAGE.md"
