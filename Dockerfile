FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY requirements /app/requirements
RUN pip install --no-cache-dir -r /app/requirements/dev.txt

COPY docker/web/entrypoint.sh /app/docker/web/entrypoint.sh
RUN chmod +x /app/docker/web/entrypoint.sh

COPY . /app

ENTRYPOINT ["/app/docker/web/entrypoint.sh"]
