FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml .
COPY uv.lock .

RUN pip install uv 
ENV UV_CACHE_DIR=/app/.cache/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen
COPY . .


EXPOSE 8000