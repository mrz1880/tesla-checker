FROM python:3.12-slim

# System dependencies for Camoufox (Firefox-based) + cron
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    libgtk-3-0 libdbus-glib-1-2 libxt6 libasound2 \
    libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 \
    libxcursor1 libxi6 libxtst6 libpango-1.0-0 libcairo2 \
    fonts-liberation fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir playwright camoufox "pydantic>=2"
RUN camoufox fetch

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
