# Base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
libpq-dev \
gcc \
&& rm -rf /var/lib/apt/lists/


# Set working directory
WORKDIR /app

# Copy requirements first
COPY requirements.txt requirements.txt

# Run pip installs
RUN pip install -r requirements.txt

# Copy code
COPY . .

# Run app
CMD sh -c "alembic upgrade head && gunicorn -k uvicorn.workers.UvicornWorker -w 2 main:app -b 0.0.0.0:8000"