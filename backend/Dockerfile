FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput
EXPOSE 8010
CMD ["gunicorn", "relaydesk.wsgi:application", "--bind", "0.0.0.0:8010", "--workers", "3"]
# CMD ["celery", "-A", "relaydesk", "worker", "-l", "info"]
