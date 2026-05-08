FROM python:3.12-slim-bookworm

WORKDIR /app

# Install only the minimal runtime deps for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Application user (non-root)
RUN groupadd -r witw && useradd -r -g witw witw

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

USER witw

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
