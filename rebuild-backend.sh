#!/bin/bash

echo "🔧 Rebuilding Backend..."
echo "============================================"

cd app

# Check Python environment
echo "1. Checking Python environment..."
if command -v python3 &> /dev/null; then
    python3 --version
else
    echo "❌ Python3 not found. Please install Python 3.9+"
    exit 1
fi

# Create virtual environment
echo "2. Setting up virtual environment..."
python3 -m venv venv 2>/dev/null || echo "Virtual environment already exists or failed"

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "3. Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Test backend
echo "4. Testing backend..."
if python -c "import fastapi, pandas, numpy, sqlalchemy, prometheus_client; print('✅ All imports successful')"; then
    echo "✅ Backend dependencies are working"
else
    echo "❌ Backend dependency check failed"
    exit 1
fi

cd ..
echo "✅ Backend rebuild completed!"
