# ML Service Dockerfile
# Supports both CPU and GPU inference

# Base image with Python 3.11
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV and YOLO
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app ./app
COPY run.py .

# Create models directory
RUN mkdir -p models

# Expose port
EXPOSE 9001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:9001/health || exit 1

# Run the application
CMD ["python", "run.py"]
