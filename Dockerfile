FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install python dependencies (runtime tối giản — không torch/streamlit/qdrant)
COPY requirements-backend.txt ./
RUN pip install --no-cache-dir -r requirements-backend.txt

# Copy application source code & built DB (data/raw & học liệu đã loại trong .dockerignore)
COPY . .

EXPOSE 8000

# Start FastAPI with uvicorn on dynamic port provided by cloud host
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
