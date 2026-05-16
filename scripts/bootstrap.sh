#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "ERROR: .env missing" >&2; exit 1
fi
# shellcheck disable=SC1091
source .env

SRC_MDF="bbdd/SOURCE_DB.MDF"
SRC_LDF="bbdd/SOURCE_DB.LDF"
DST_MDF="data/SOURCE_DB.MDF"
DST_LDF="data/SOURCE_DB.LDF"

if [[ ! -f "$SRC_MDF" || ! -f "$SRC_LDF" ]]; then
  echo "ERROR: originals not found in bbdd/" >&2; exit 1
fi

if [[ ! -f "$DST_MDF" || ! -f "$DST_LDF" ]]; then
  echo ">> Copying MDF/LDF to data/ (working copy)..."
  cp -p "$SRC_MDF" "$DST_MDF"
  cp -p "$SRC_LDF" "$DST_LDF"
  echo ">> Copy done."
else
  echo ">> data/ already populated, skipping copy."
fi

echo ">> Setting permissions for mssql UID 10001..."
chmod 660 "$DST_MDF" "$DST_LDF"

echo ">> Bringing up docker compose..."
docker compose up -d

echo ">> Waiting for mssql healthcheck..."
for i in {1..60}; do
  status=$(docker inspect -f '{{.State.Health.Status}}' gesden-mssql 2>/dev/null || echo "starting")
  if [[ "$status" == "healthy" ]]; then
    echo ">> mssql healthy."
    break
  fi
  echo "   [$i/60] status=$status"
  sleep 5
done

if [[ "$status" != "healthy" ]]; then
  echo "ERROR: mssql not healthy. Logs:" >&2
  docker logs --tail 80 gesden-mssql >&2
  exit 1
fi

# Fix file ownership inside container so sqlservr can write to MDF/LDF
echo ">> Fixing file ownership inside container..."
docker exec -u 0 gesden-mssql chown mssql:root /var/opt/mssql/gesden/SOURCE_DB.MDF /var/opt/mssql/gesden/SOURCE_DB.LDF

echo ">> Running attach script..."
docker exec gesden-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$SA_PASSWORD" -C -b -i /sql/01-attach.sql

echo
echo ">> DONE."
echo "   SQL Server:  localhost:1433  (user: sa)"
echo "   Metabase:    http://localhost:3001"
