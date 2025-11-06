#!/bin/bash

# Setup iris-ml Conda Environment for ML Service (with MPS GPU support)
# This creates a separate environment optimized for running the ML service on macOS with GPU

set -e

echo "=========================================="
echo "  Setting up iris-ml Environment"
echo "  For ML Service with MPS GPU Support"
echo "=========================================="
echo ""

# Get conda base
CONDA_BASE=$(conda info --base 2>/dev/null || echo "")
if [ -z "$CONDA_BASE" ]; then
    echo "❌ Error: conda not found"
    echo "   Please install Anaconda or Miniconda first"
    exit 1
fi

# Source conda
source "$CONDA_BASE/etc/profile.d/conda.sh"

echo "✓ Found conda"
echo ""

# Check if iris-ml environment already exists
if conda env list | grep -q "^iris-ml "; then
    echo "⚠ iris-ml environment already exists"
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing iris-ml environment..."
        conda deactivate 2>/dev/null || true
        conda env remove -n iris-ml -y
    else
        echo "Using existing environment"
        conda activate iris-ml
        skip_create=true
    fi
fi

# Create environment if needed
if [ "$skip_create" != "true" ]; then
    echo "Creating iris-ml conda environment with Python 3.11..."
    conda create -n iris-ml python=3.11 -y
    echo "✓ Environment created"
    echo ""
fi

# Activate environment
echo "Activating iris-ml environment..."
conda activate iris-ml
echo "✓ Environment activated"
echo ""

# Install ML service dependencies
echo "Installing ML Service dependencies..."
echo "This includes PyTorch with MPS support for Apple Silicon GPU"
echo ""

cd ml-service

echo "Installing packages:"
echo "  - PyTorch with MPS (Metal Performance Shaders) support"
echo "  - Ultralytics YOLO"
echo "  - OpenCV and other dependencies"
echo ""

# Install dependencies
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "  Verifying Installation & GPU Support"
echo "=========================================="
echo ""

# Verify critical packages and GPU
python << 'EOF'
import sys

packages = []
errors = []

print("Checking installed packages...\n")

# Check PyTorch
try:
    import torch
    packages.append(f"✓ PyTorch {torch.__version__}")

    # Check MPS (Metal Performance Shaders) support
    if torch.backends.mps.is_available():
        packages.append(f"  ✓ MPS (GPU) available and enabled!")
        packages.append(f"  ✓ Device: Apple Silicon GPU (Metal)")
    else:
        packages.append(f"  ℹ MPS not available, using CPU")

except ImportError as e:
    errors.append(f"✗ PyTorch: {e}")

# Check Ultralytics
try:
    import ultralytics
    from ultralytics import YOLO
    packages.append(f"✓ Ultralytics YOLO")
except ImportError as e:
    errors.append(f"✗ Ultralytics: {e}")

# Check OpenCV
try:
    import cv2
    packages.append(f"✓ OpenCV {cv2.__version__}")
except ImportError as e:
    errors.append(f"✗ OpenCV: {e}")

# Check FastAPI
try:
    import fastapi
    packages.append(f"✓ FastAPI {fastapi.__version__}")
except ImportError as e:
    errors.append(f"✗ FastAPI: {e}")

# Print results
for pkg in packages:
    print(pkg)

if errors:
    print("\nErrors:")
    for err in errors:
        print(err)
    sys.exit(1)
else:
    print("\n✓ All ML packages installed successfully!")
    sys.exit(0)
EOF

VERIFY_STATUS=$?

cd ..

echo ""

if [ $VERIFY_STATUS -eq 0 ]; then
    # Update .env to use mps if available
    if [ -f "ml-service/.env" ]; then
        if grep -q "DEVICE=cpu" ml-service/.env; then
            read -p "Enable MPS GPU in ml-service/.env? (Y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                sed -i.bak 's/DEVICE=cpu/DEVICE=mps/' ml-service/.env
                echo "✓ Updated ml-service/.env to use MPS GPU"
            fi
        fi
    else
        echo "Creating ml-service/.env with MPS GPU enabled..."
        cp ml-service/.env.example ml-service/.env
        sed -i.bak 's/DEVICE=cpu/DEVICE=mps/' ml-service/.env
        echo "✓ Created ml-service/.env with MPS GPU"
    fi

    echo ""
    echo "=========================================="
    echo "  iris-ml Environment Ready!"
    echo "=========================================="
    echo ""
    echo "The ML service environment is set up with:"
    echo "  - Python 3.11"
    echo "  - PyTorch with MPS (GPU) support"
    echo "  - Ultralytics YOLOv11"
    echo "  - All ML dependencies"
    echo ""
    echo "To use the ML service:"
    echo "  conda activate iris-ml"
    echo "  cd ml-service"
    echo "  python run.py"
    echo ""
    echo "Or use the dual-environment startup script:"
    echo "  ./start_services.sh"
    echo ""
    echo "Note: MPS GPU acceleration will be used automatically"
    echo "      You can verify in the logs when the service starts"
    echo ""
else
    echo "=========================================="
    echo "  Installation Issues Detected"
    echo "=========================================="
    echo ""
    echo "Some packages failed to install."
    echo "Please check the error messages above."
    exit 1
fi
