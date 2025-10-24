FROM python:3.11-slim

# create non-root user
RUN adduser --disabled-password --gecos "" appuser || true
WORKDIR /app

# install build deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# copy application
COPY src /app/src
COPY publisher /app/publisher
COPY tests /app/tests

USER appuser

EXPOSE 8080

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
FROM python:3.11-slim

RUN adduser --disabled-password --gecos "" appuser || true
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy app
# copy the whole project so tests and docker-compose files are available inside the image
COPY . /app

USER appuser

EXPOSE 8080

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
