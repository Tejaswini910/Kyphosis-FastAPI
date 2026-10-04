FROM python:3.12-slim

WORKDIR /app
COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt
COPY main.py .
COPY static ./static
COPY ["data/FASTAP/kyphosis (1).csv", "/app/data/FASTAP/kyphosis (1).csv"]

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]