FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY uv.lock .

RUN pip install uv 
ENV UV_CACHE_DIR=/app/.cache/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen
COPY . .


EXPOSE 8000