FROM python:3.12-slim

# psycopg2 needs libpq at build time; kept minimal otherwise.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# docker-compose.yml (dev) and docker-compose.prod.yml override this
# command explicitly (--reload for dev, gunicorn workers for prod) --
# this default is a sane standalone fallback.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
