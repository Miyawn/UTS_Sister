FROM python:3.11-slim

# Create non-root user and workdir
RUN adduser --disabled-password --gecos "" appuser || true
WORKDIR /app

# Install dependencies (copy requirements first for build cache)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy project files
COPY . /app

# Ensure appuser owns the workspace
RUN chown -R appuser:appuser /app || true

USER appuser

EXPOSE 8080

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
