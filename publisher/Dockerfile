FROM python:3.11-slim
WORKDIR /publisher
COPY main.py /publisher/main.py
RUN pip install --no-cache-dir httpx
CMD ["python", "main.py"]
