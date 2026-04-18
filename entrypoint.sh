#!/bin/sh
set -e

# Write env vars to a file so cron can access them
env | grep -E '^(NTFY_|RESULTS_DIR|TZ|HOME|PATH)' > /app/.env
echo "PYTHONUNBUFFERED=1" >> /app/.env

# Create cron schedule (8h30 and 18h30 Europe/Paris)
CRON_SCHEDULE="${CRON_SCHEDULE:-30 8,18 * * *}"

cat > /etc/cron.d/tesla-check << EOF
${CRON_SCHEDULE} root cd /app && set -a && . /app/.env && set +a && python main.py >> /data/cron.log 2>&1
EOF

chmod 0644 /etc/cron.d/tesla-check
crontab /etc/cron.d/tesla-check

echo "$(date) - Tesla Checker started"
echo "  Schedule: ${CRON_SCHEDULE}"
echo "  Ntfy topic: ${NTFY_TOPIC:-NOT SET}"
echo ""

# Run once at startup
echo "=== Initial check ==="
python main.py 2>&1 || true
echo ""

# Start cron in foreground
echo "=== Cron daemon started ==="
exec cron -f
