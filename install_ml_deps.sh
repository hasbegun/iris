#!/bin/bash

# Install ML Service Dependencies for Conda Environment
# Usage: ./install_ml_deps.sh

set -e

echo "=========================================="
echo "  Installing ML Service Dependencies"
echo "  Conda Environment: iris"
echo "=========================================="
echo ""

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "❌ Error: conda not found"
    echo "   Please install Anaconda or Miniconda first"
    exit 1
fi

# Check if iris environment exists
if ! conda env list | grep -q "^iris "; then
    echo "❌ Error: conda environment 'iris' not found"
    echo ""
    echo "Available environments:"
    conda env list
    echo ""
    echo "To create the environment:"
    echo "  conda create -n iris python=3.11"
    exit 1
fi

echo "✓ Found conda environment 'iris'"
echo ""

# Get the conda source command
CONDA_BASE=$(conda info --base)
source "$CONDA_BASE/etc/profile.d/conda.sh"

# Activate environment
echo "Activating conda environment 'iris'..."
conda activate iris

echo "✓ Environment activated"
echo ""

# Check Python version
PYTHON_VERSION=$(python --version)
echo "Python version: $PYTHON_VERSION"
echo ""

# Install ML Service dependencies
echo "Installing ML Service dependencies..."
echo "This may take 5-10 minutes depending on your internet connection"
echo ""

cd ml-service

echo "Installing packages:"
echo "  - PyTorch (deep learning framework)"
echo "  - Ultralytics YOLO (object detection)"
echo "  - OpenCV (image processing)"
echo "  - FastAPI, Uvicorn (web framework)"
echo "  - Other utilities"
echo ""

# Install dependencies
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "  Verifying Installation"
echo "=========================================="
echo ""

# Verify critical packages
python << 'EOF'
import sys

packages = []
errors = []

print("Checking installed packages...\n")

# Check PyTorch
try:
    import torch
    packages.append(f"✓ PyTorch {torch.__version__}")
    cuda_available = torch.cuda.is_available()
    if cuda_available:
        packages.append(f"  ✓ CUDA available: {torch.cuda.get_device_name(0)}")
    else:
        packages.append(f"  ℹ CUDA not available (using CPU)")
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

# Check Pillow
try:
    import PIL
    packages.append(f"✓ Pillow (PIL) {PIL.__version__}")
except ImportError as e:
    errors.append(f"✗ Pillow: {e}")

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
    echo "=========================================="
    echo "  Installation Complete!"
    echo "=========================================="
    echo ""
    echo "ML Service dependencies are installed in 'iris' conda environment"
    echo ""
    echo "Next steps:"
    echo "  1. Make sure Ollama is running with required models:"
    echo "     ollama pull llava:latest"
    echo "     ollama pull gemma3:latest"
    echo ""
    echo "  2. Start the services:"
    echo "     conda activate iris"
    echo "     ./start_services.sh"
    echo ""
    echo "  3. Run tests:"
    echo "     conda activate iris"
    echo "     python test_integration.py"
    echo ""
else
    echo "=========================================="
    echo "  Installation Issues Detected"
    echo "=========================================="
    echo ""
    echo "Some packages failed to install."
    echo "Please check the error messages above."
    echo ""
    echo "You can try installing manually:"
    echo "  conda activate iris"
    echo "  cd ml-service"
    echo "  pip install -r requirements.txt"
    echo ""
    exit 1
fi
