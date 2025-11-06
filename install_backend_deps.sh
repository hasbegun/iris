#!/bin/bash

# Install Backend Dependencies in iris environment

CONDA_BASE=$(conda info --base)
source "$CONDA_BASE/etc/profile.d/conda.sh"

conda activate iris

cd backend
echo "Installing backend dependencies in iris environment..."
pip install -r requirements.txt

echo "✓ Backend dependencies installed"
