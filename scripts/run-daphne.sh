ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings}"
BIND="${DAPHNE_BIND:-0.0.0.0}"
PORT="${DAPHNE_PORT:-8000}"

echo "Daphne: http://${BIND}:${PORT}/ (config.asgi:application)"

exec "$ROOT/env/bin/python" -m daphne -b "$BIND" -p "$PORT" config.asgi:application
