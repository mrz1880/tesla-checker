#!/bin/bash
set -euo pipefail

IMAGE="ghcr.io/mrz1880/tesla-checker"
TAG="${1:-latest}"

NAS_HOST="nas-ugreen"
STACK_DIR="/volume1/docker/stacks/tesla-checker"

echo "Building image ${IMAGE}:${TAG}..."
docker buildx build --platform linux/amd64 -t "${IMAGE}:${TAG}" --push .

echo "Image pushed to GHCR."

echo "Deploying to NAS..."
ssh "$NAS_HOST" "mkdir -p ${STACK_DIR}"
cat deploy/compose.yml | ssh "$NAS_HOST" "cat > ${STACK_DIR}/compose.yml"

# Copy .env if it doesn't exist yet on NAS
ssh "$NAS_HOST" "test -f ${STACK_DIR}/.env || echo 'NTFY_TOPIC=tesla-occasion-CHANGE-ME' > ${STACK_DIR}/.env"

ssh "$NAS_HOST" "cd ${STACK_DIR} && docker compose pull && docker compose up -d"

echo "Deploy complete."
echo ""
echo "REMINDER: Edit .env on NAS if first deploy:"
echo "  ssh ${NAS_HOST} 'vi ${STACK_DIR}/.env'"
