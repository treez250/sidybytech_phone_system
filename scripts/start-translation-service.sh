#!/bin/bash
# Start GPU Translation Service
# Run this on linux-gpu-01 (192.168.1.178)

set -e

echo "=== Starting GPU Translation Service ==="
echo ""

# Check if we're on the right server
HOSTNAME=$(hostname)
if [[ "$HOSTNAME" != "linux-gpu-01" ]]; then
    echo "⚠️  WARNING: This should run on linux-gpu-01 (192.168.1.178)"
    echo "Current hostname: $HOSTNAME"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check GPU
echo "Checking GPU..."
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ nvidia-smi not found. Is NVIDIA driver installed?"
    exit 1
fi

nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
echo ""

# Check Python environment
if [ ! -d "translation-venv" ]; then
    echo "❌ Virtual environment not found"
    echo "Run: python3 -m venv translation-venv"
    exit 1
fi

# Activate environment
source translation-venv/bin/activate

# Check dependencies
echo "Checking dependencies..."
python3 -c "import torch; import whisper; import transformers" 2>/dev/null || {
    echo "❌ Missing dependencies"
    echo "Run: pip install -r services/requirements-production.txt"
    exit 1
}

# Check CUDA
echo "Checking CUDA..."
python3 -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"
python3 -c "import torch; print(f'CUDA Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
echo ""

# Check port availability
echo "Checking port 4000..."
if lsof -Pi :4000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 4000 already in use"
    lsof -i :4000
    read -p "Kill existing process? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        lsof -ti:4000 | xargs kill -9
        echo "Killed existing process"
    else
        exit 1
    fi
fi

# Start service
echo ""
echo "=== Starting Translation Service ==="
echo "Press Ctrl+C to stop"
echo ""

cd services
python3 translation-service-gpu.py
