#!/bin/bash

CONDA_BASE=$(conda info --base)
source "$CONDA_BASE/etc/profile.d/conda.sh"

conda activate iris

cd backend
nohup python run.py > ../backend.log 2>&1 &
echo "Backend started with PID: $!"
