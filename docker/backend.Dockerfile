FROM python:3.12-slim

WORKDIR /workspace

# Install system dependencies (needed for compiling python modules and postgres client)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend app files
COPY backend/ /workspace/backend/
COPY uploads/ /workspace/uploads/
COPY reports/ /workspace/reports/

# Set Python Path to include workspace root
ENV PYTHONPATH=/workspace

EXPOSE 8000

# Start application using uvicorn
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
