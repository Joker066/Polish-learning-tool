FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONPYCACHEPREFIX=/app/.pycache \
    TZ=Asia/Taipei \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl tzdata && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
RUN python -m compileall -q /app

RUN mkdir -p /app/seed && cp -f databases/app.db /app/seed/app.db
RUN mkdir -p /app/databases /app/data && chown -R 1000:1000 /app
USER 1000:1000

COPY --chown=1000:1000 docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s \
  CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "-w", "2", "-k", "gthread", "-t", "60", "--max-requests", "1000", "--max-requests-jitter", "100", "-b", "0.0.0.0:8000", "app:app"]
