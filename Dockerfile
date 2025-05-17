# Base image with CUDA support
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

# Set working directory
WORKDIR /app

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies - fixed path and improved error handling
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    libhdf5-dev \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /app/face_database

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY .env ./.env
COPY credentials.json ./credentials.json

# Create the face_database directory if it doesn't exist
RUN mkdir -p face_database

# Expose the port your FastAPI app will run on
EXPOSE 5016

# Set environment variable to use GPU
ENV CUDA_VISIBLE_DEVICES=0

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5016"]