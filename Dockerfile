# Use the official Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (required for some Python C-extensions like pandas/numpy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy dependencies list
COPY requirements.txt /app/

# Install python dependencies system-wide within the container using uv
RUN uv pip install --system -r requirements.txt

# Copy the rest of the application
COPY . /app/

# Ensure the data directory exists for SQLite
RUN mkdir -p /app/data

# Default command
CMD ["python", "main.py"]
