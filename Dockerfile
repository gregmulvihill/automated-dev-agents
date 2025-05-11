FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY setup.py ./
COPY README.md ./

# Install the package in development mode
RUN pip install -e .[dev] --no-cache-dir

# Copy the rest of the code
COPY . .

# Create necessary directories
RUN mkdir -p logs

# Command to run on container start
CMD ["python", "-m", "src.main", "--config", "config/default.json"]