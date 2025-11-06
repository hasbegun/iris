#!/bin/bash

# Start YOLO ML Service Integration
# This script starts both ML service and Backend in separate terminals
# For use with conda environment 'iris'

set -e

echo "=========================================="
echo "  YOLO ML Service - Startup Script"
echo "  Conda Environment: iris"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -d "ml-service" ] || [ ! -d "backend" ]; then
    echo "❌ Error: Must run from project root directory"
    echo "   Current directory: $(pwd)"
    exit 1
fi

# Get conda base and source it
CONDA_BASE=$(conda info --base 2>/dev/null || echo "")
if [ -z "$CONDA_BASE" ]; then
    echo "⚠ Warning: conda not detected, using system python"
    USE_CONDA=false
else
    source "$CONDA_BASE/etc/profile.d/conda.sh"
    USE_CONDA=true

    # Check if iris and iris-ml environments exist
    if conda env list | grep -q "^iris "; then
        echo "✓ Found conda environment 'iris' (for backend)"
    else
        echo "⚠ Warning: conda environment 'iris' not found"
        echo "   Backend will use current environment"
    fi

    if conda env list | grep -q "^iris-ml "; then
        echo "✓ Found conda environment 'iris-ml' (for ML service with GPU)"
    else
        echo "⚠ Warning: conda environment 'iris-ml' not found"
        echo "   Run ./setup_ml_env.sh to create it with MPS GPU support"
        echo "   ML service will use 'iris' environment instead"
    fi
    echo ""
fi

# Function to check if a service is running
check_service() {
    local url=$1
    local name=$2

    if curl -s "$url" > /dev/null 2>&1; then
        echo "✓ $name is already running at $url"
        return 0
    else
        echo "✗ $name is not running"
        return 1
    fi
}

echo "Checking if services are already running..."
echo ""

ML_RUNNING=false
BACKEND_RUNNING=false

if check_service "http://localhost:9001/health" "ML Service"; then
    ML_RUNNING=true
fi

if check_service "http://localhost:9000/api/health" "Backend"; then
    BACKEND_RUNNING=true
fi

echo ""

# If both are running, we're done
if [ "$ML_RUNNING" = true ] && [ "$BACKEND_RUNNING" = true ]; then
    echo "✓ All services are already running!"
    echo ""
    echo "  ML Service:  http://localhost:9001"
    echo "  Backend:     http://localhost:9000"
    echo "  Docs:        http://localhost:9000/docs"
    echo ""
    exit 0
fi

echo "Starting services..."
echo ""

# Start ML Service if not running
if [ "$ML_RUNNING" = false ]; then
    echo "Starting ML Service..."

    # Check if .env exists
    if [ ! -f "ml-service/.env" ]; then
        echo "  Creating .env from template..."
        cp ml-service/.env.example ml-service/.env
    fi

    # Activate iris-ml environment if available, otherwise use iris
    if [ "$USE_CONDA" = true ]; then
        if conda env list | grep -q "^iris-ml "; then
            echo "  Activating iris-ml environment (with GPU support)..."
            conda activate iris-ml
        else
            echo "  Activating iris environment..."
            conda activate iris
        fi
    fi

    # Start in background
    cd ml-service
    echo "  Installing dependencies (if needed)..."
    pip install -q -r requirements.txt > /dev/null 2>&1 || true

    echo "  Starting ML service on port 9001..."
    nohup python run.py > ../ml-service.log 2>&1 &
    ML_PID=$!
    echo "  ML Service PID: $ML_PID"
    cd ..

    # Wait a bit for startup
    echo "  Waiting for ML service to start..."
    sleep 3

    # Check if it started
    if check_service "http://localhost:9001/health" "ML Service"; then
        echo "  ✓ ML Service started successfully"
    else
        echo "  ✗ ML Service failed to start. Check ml-service.log"
    fi
    echo ""
fi

# Start Backend if not running
if [ "$BACKEND_RUNNING" = false ]; then
    echo "Starting Backend..."

    # Check if .env exists
    if [ ! -f "backend/.env" ]; then
        echo "  Creating .env from template..."
        cp backend/.env.example backend/.env
    fi

    # Activate iris environment
    if [ "$USE_CONDA" = true ]; then
        if conda env list | grep -q "^iris "; then
            echo "  Activating iris environment..."
            conda activate iris
        fi
    fi

    # Start in background
    cd backend
    echo "  Installing dependencies (if needed)..."
    pip install -q -r requirements.txt > /dev/null 2>&1 || true

    echo "  Starting backend on port 9000..."
    nohup python run.py > ../backend.log 2>&1 &
    BACKEND_PID=$!
    echo "  Backend PID: $BACKEND_PID"
    cd ..

    # Wait a bit for startup
    echo "  Waiting for backend to start..."
    sleep 3

    # Check if it started
    if check_service "http://localhost:9000/api/health" "Backend"; then
        echo "  ✓ Backend started successfully"
    else
        echo "  ✗ Backend failed to start. Check backend.log"
    fi
    echo ""
fi

echo "=========================================="
echo "  Services Started!"
echo "=========================================="
echo ""
echo "  ML Service:  http://localhost:9001"
echo "  Backend:     http://localhost:9000"
echo "  API Docs:    http://localhost:9000/docs"
echo "  ML Docs:     http://localhost:9001/docs"
echo ""
echo "Logs:"
echo "  ML Service:  tail -f ml-service.log"
echo "  Backend:     tail -f backend.log"
echo ""
echo "To stop services:"
echo "  pkill -f 'python run.py'"
echo ""
echo "Ready to test! Run: python test_integration.py"
echo ""
