#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/encuentra-opensearch"

if command -v dnf >/dev/null 2>&1; then
  dnf update -y
  dnf install -y docker docker-compose-plugin || dnf install -y docker
elif command -v yum >/dev/null 2>&1; then
  yum update -y
  yum install -y docker docker-compose-plugin || yum install -y docker
elif command -v apt-get >/dev/null 2>&1; then
  apt-get update -y
  apt-get install -y ca-certificates curl docker.io
  apt-get install -y docker-compose-plugin || apt-get install -y docker-compose-v2 || apt-get install -y docker-compose || true
else
  echo "Unsupported OS: install Docker manually." >&2
  exit 1
fi

systemctl enable --now docker

if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  COMPOSE_CMD=()
fi

mkdir -p "${APP_DIR}"

cat > "${APP_DIR}/docker-compose.yml" <<'EOF'
services:
  opensearch:
    image: opensearchproject/opensearch:3
    container_name: encuentra-opensearch
    restart: unless-stopped
    ports:
      - "9200:9200"
      - "9600:9600"
    environment:
      discovery.type: single-node
      plugins.security.disabled: "true"
      OPENSEARCH_JAVA_OPTS: "-Xms1g -Xmx1g"
    ulimits:
      memlock:
        soft: -1
        hard: -1
      nofile:
        soft: 65536
        hard: 65536
    volumes:
      - opensearch-data:/usr/share/opensearch/data

volumes:
  opensearch-data:
EOF

cd "${APP_DIR}"
if [ "${#COMPOSE_CMD[@]}" -gt 0 ]; then
  "${COMPOSE_CMD[@]}" up -d
else
  docker volume create opensearch-data
  docker rm -f encuentra-opensearch >/dev/null 2>&1 || true
  docker run -d --name encuentra-opensearch \
    --restart unless-stopped \
    -p 9200:9200 -p 9600:9600 \
    -e discovery.type=single-node \
    -e plugins.security.disabled=true \
    -e OPENSEARCH_JAVA_OPTS="-Xms1g -Xmx1g" \
    --ulimit memlock=-1:-1 \
    --ulimit nofile=65536:65536 \
    -v opensearch-data:/usr/share/opensearch/data \
    opensearchproject/opensearch:3
fi
