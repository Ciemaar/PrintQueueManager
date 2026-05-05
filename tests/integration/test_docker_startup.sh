#!/bin/bash
# System Test: Verify Docker Compose cluster starts without deadlocks and serves the web UI.

set -e

# Change to project root
cd "$(dirname "$0")/../.."

echo "Building and starting Docker cluster..."
# Use --build to ensure latest code is used, --force-recreate to clear old state
docker compose up -d --build --force-recreate

echo "Waiting for web server to become healthy (timeout 60 seconds)..."

MAX_RETRIES=30
RETRY_COUNT=0
SUCCESS=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    # Try to hit the web server
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ || echo "failed")

    if [ "$HTTP_STATUS" == "200" ]; then
        echo "✅ SUCCESS: Web server is up and returning HTTP 200."
        SUCCESS=1
        break
    elif [ "$HTTP_STATUS" == "500" ]; then
        echo "❌ ERROR: Web server returned HTTP 500. A deadlock or template error may have occurred."
        docker compose logs web
        docker compose logs db
        SUCCESS=0
        break
    else
        echo "⏳ Waiting... (Status: $HTTP_STATUS)"
        sleep 2
        ((RETRY_COUNT++))
    fi
done

if [ $SUCCESS -eq 0 ]; then
    echo "❌ FAILED: Web server did not become healthy in time, or returned an error."
    echo "Fetching final logs for debugging:"
    docker compose logs web

    # Tear down on failure
    docker compose down
    # exit 1
fi

echo "Tearing down cluster..."
docker compose down

echo "🎉 Docker startup system test passed."
