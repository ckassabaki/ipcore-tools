#!/bin/bash
# IPCore Tools Registry - Installation Script

set -e

echo "🔧 Installing IPCore Tools Registry..."

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Must run from ipcore-tools directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
mkdir -p cache screenshots

# Initialize database
echo "🗄️  Initializing database..."
python -c "from db_tools_registry import init_db; init_db()"

# Run crawlers to discover tools
echo "🔍 Running auto-discovery..."
python crawlers/run_all.py

echo ""
echo "✅ Installation complete!"
echo ""
echo "To start the server:"
echo "  source .venv/bin/activate"
echo "  uvicorn app:app --port 8090 --reload"
echo ""
echo "Or install as systemd service:"
echo "  ./deploy/install_service.sh"
echo ""
