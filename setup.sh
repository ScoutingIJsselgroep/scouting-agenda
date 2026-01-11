#!/bin/bash
# Quick setup script for scouting-agenda

set -e

echo "🚀 Setting up Scouting Calendar system..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "✓ Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create output directory
mkdir -p output

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy secrets.yaml.example to secrets.yaml"
echo "2. Edit secrets.yaml with your ICS URLs"
echo "3. Run: python sync.py"
echo "4. Start server: python run_server.py"
echo ""
echo "Or run manually:"
echo "  source .venv/bin/activate"
echo "  python sync.py"
echo "  python run_server.py"
