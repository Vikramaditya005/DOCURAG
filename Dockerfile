FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System libraries needed by OpenCV / EasyOCR
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# CPU-only PyTorch first (the default Linux wheel pulls GBs of GPU libraries)
RUN pip install --upgrade pip \
    && pip install --index-url https://download.pytorch.org/whl/cpu torch

# Python dependencies (requirements.txt must include gunicorn, whitenoise, python-docx)
COPY requirements.txt .
RUN pip install --prefer-binary -r requirements.txt

# Copy the project
COPY . .

# Index, uploads, database and model cache live on the /data volume
ENV PYTHONPATH=/app \
    DJANGO_SETTINGS_MODULE=config.settings \
    DOCURAG_STORAGE=/data/storage \
    SQLITE_PATH=/data/db.sqlite3 \
    HF_HOME=/data/hf_cache

# Collect static files (throwaway SECRET_KEY used only at build time)
RUN SECRET_KEY=build-only python backend/manage.py collectstatic --noinput

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health/', timeout=8)" || exit 1

# One worker on purpose: the engine and FAISS index are cached per process
CMD ["sh", "-c", "mkdir -p /data/storage && cd backend && python manage.py migrate --noinput && gunicorn config.wsgi:application --workers 1 --threads 4 --timeout 300 --access-logfile - --bind 0.0.0.0:8000"]
