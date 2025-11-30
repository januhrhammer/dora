# Backend Dockerfile for FastAPI application
# This creates a Docker image that runs the medicine tracker API

FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose port 8000 for the API
EXPOSE 8000

# Create a startup script that runs migrations then starts the app
RUN echo '#!/bin/bash\n\
echo "Running database migrations..."\n\
alembic upgrade head\n\
echo "Starting FastAPI application..."\n\
uvicorn app.main:app --host 0.0.0.0 --port 8000\n\
' > /app/start.sh && chmod +x /app/start.sh

# Run the startup script
# This will apply any pending database migrations before starting the server
CMD ["/bin/bash", "/app/start.sh"]
