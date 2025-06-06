FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ipmitool \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose the port the app runs on
EXPOSE 5010

# Run the application
CMD ["python", "app.py"]