FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install basic build deps for common Python packages (psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app

# Ensure logs directory exists for the rotating file handler
RUN mkdir -p /app/logs

EXPOSE 8000

# Run the FastAPI app using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
