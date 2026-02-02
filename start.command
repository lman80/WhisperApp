#!/bin/bash
# WhisperApp Launch Script
# Usage: ./start.command

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "🎤 Starting WhisperApp..."

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10+."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    
    echo "📥 Installing dependencies (this may take a few minutes on first run)..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Check for ffmpeg (required by some audio processing)
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  Warning: ffmpeg is not installed. Some features may not work."
    echo "   Install with: brew install ffmpeg"
fi

# First run: Grant accessibility permissions reminder
if [ ! -f "$HOME/.whisperapp/.initialized" ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔐 IMPORTANT: First Run Setup"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "WhisperApp needs Accessibility permissions to:"
    echo "  • Detect the push-to-talk hotkey (Right ⌘)"
    echo "  • Type transcribed text into apps"
    echo ""
    echo "When prompted, go to:"
    echo "  System Settings → Privacy & Security → Accessibility"
    echo "  Then enable access for Terminal (or your terminal app)"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    mkdir -p "$HOME/.whisperapp"
    touch "$HOME/.whisperapp/.initialized"
fi

# Download models on first run (background notice)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎤 WhisperApp - Local Voice-to-Text"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Usage:"
echo "  • Hold Right ⌘ to record"
echo "  • Release to transcribe and paste"
echo "  • Click menu bar icon 🎤 for history/stats"
echo ""
echo "Starting..."
echo ""

# Run the app
python -m whisperapp
