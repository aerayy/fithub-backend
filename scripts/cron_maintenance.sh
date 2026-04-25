#!/bin/bash
# Saatlik maintenance cron'u — Render Cron Job ile çağrılır.
# Required env: ADMIN_API_KEY, BACKEND_URL (default: production)

set -e

BACKEND_URL="${BACKEND_URL:-https://fithub-backend-jd40.onrender.com}"

if [ -z "$ADMIN_API_KEY" ]; then
  echo "ERROR: ADMIN_API_KEY env required"
  exit 1
fi

echo "=== Maintenance run @ $(date -u +'%Y-%m-%dT%H:%M:%SZ') ==="

echo ""
echo "[1/2] Zamanlanmış taslakları aktive ediyorum..."
curl -fsS -X POST "$BACKEND_URL/admin/maintenance/activate-scheduled-drafts" \
  -H "X-Admin-Key: $ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  || echo "  WARN: activate-scheduled-drafts failed (continuing)"
echo ""

echo "[2/2] Süresi geçmiş abonelikleri expire ediyorum..."
curl -fsS -X POST "$BACKEND_URL/admin/maintenance/expire-subscriptions" \
  -H "X-Admin-Key: $ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  || echo "  WARN: expire-subscriptions failed (continuing)"
echo ""

echo "=== Maintenance done @ $(date -u +'%Y-%m-%dT%H:%M:%SZ') ==="
