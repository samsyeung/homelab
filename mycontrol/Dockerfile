FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ipmitool \
    sshpass \
    ttyd \
    iputils-ping \
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

# Create a non-root user for security
RUN useradd -m -u 1000 mycontrol && chown -R mycontrol:mycontrol /app
USER mycontrol

# Expose the port the app runs on and ttyd port range
EXPOSE 5010
EXPOSE 7681-7781

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV MYCONTROL_INTERACTIVE=false

# Run the application
CMD ["python", "app.py"]