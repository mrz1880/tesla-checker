FROM python:3.12-slim

# Playwright system dependencies + cron
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libatspi2.0-0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2 libwayland-client0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir playwright
RUN playwright install chromium

COPY src/ src/
COPY main.py .
COPY pyproject.toml .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

VOLUME /data

ENV TZ=Europe/Paris
ENV RESULTS_DIR=/data
ENV NTFY_TOPIC=""
ENV NTFY_URL="https://ntfy.sh"
ENV CRON_SCHEDULE="30 8,18 * * *"

ENTRYPOINT ["./entrypoint.sh"]
