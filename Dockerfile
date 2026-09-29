FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=10000
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-crosextra-carlito fonts-liberation \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd --create-home --uid 10001 rolefit && mkdir -p /app/data && chown rolefit:rolefit /app/data
COPY --chown=rolefit:rolefit app ./app
USER rolefit
EXPOSE 10000
# Single process/worker is intentional for the personal-use background queue.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1 --no-access-log"]
