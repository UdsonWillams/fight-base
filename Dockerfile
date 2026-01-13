# Pull official latest Python Docker image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONOPTIMIZE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies with poetry
RUN apt-get update && apt-get install -y \
    build-essential \
    gettext \
    libpq-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    cron

# Copy all files
COPY . .
COPY frontend /app/frontend
# Install Python dependencies
RUN python3 -m pip install --upgrade setuptools wheel
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Set the server port
EXPOSE 8000

# Start up the backend server
# Start up the backend server (using PORT env var if available, default to 8080)
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"
