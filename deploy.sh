#!/usr/bin/env bash
set -euo pipefail

# LightLayer Dashboard — Production Deploy Script
# Usage: DOMAIN=app.lightlayer.dev ./deploy.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Validate required env vars
: "${DOMAIN:?Set DOMAIN (e.g. app.lightlayer.dev)}"

# Generate secrets if .env.prod doesn't exist
if [ ! -f .env.prod ]; then
    echo "Creating .env.prod with generated secrets..."
    cat > .env.prod <<EOF
DOMAIN=${DOMAIN}
POSTGRES_PASSWORD=$(openssl rand -hex 24)
SECRET_KEY=$(openssl rand -hex 32)
EOF
    echo "⚠️  .env.prod created — review it, then re-run this script."
    exit 0
fi

# Source the env file
export $(grep -v '^#' .env.prod | xargs)

echo "🚀 Deploying LightLayer Dashboard to ${DOMAIN}..."

# Pull latest and build
git pull --ff-only || true
docker compose -f docker-compose.prod.yml build

# Run migrations and start services
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "✅ Dashboard deployed!"
echo "   URL: https://${DOMAIN}"
echo ""
echo "   Logs:  docker compose -f docker-compose.prod.yml logs -f"
echo "   Stop:  docker compose -f docker-compose.prod.yml down"
