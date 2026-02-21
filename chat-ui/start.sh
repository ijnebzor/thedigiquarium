#!/bin/bash
cd "$(dirname "$0")"

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ] && [ ! -f "../.anthropic_key" ]; then
    echo "⚠️  No Anthropic API key found!"
    echo "   Option 1: export ANTHROPIC_API_KEY=your-key"
    echo "   Option 2: echo 'your-key' > ../.anthropic_key"
    exit 1
fi

# Install deps if needed
pip3 install -q flask anthropic 2>/dev/null

# Run
python3 app.py
