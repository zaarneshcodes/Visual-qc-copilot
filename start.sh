#!/usr/bin/env bash
# Starts the API in the background, waits until it answers, then runs the dashboard in front.
set -e
PORT="${PORT:-7860}"
export API_URL="${API_URL:-http://127.0.0.1:8000}"

uvicorn qc_copilot.api:app --host 127.0.0.1 --port 8000 &

echo "Waiting for the API to come up..."
for i in $(seq 1 90); do
  if curl -fs http://127.0.0.1:8000/health > /dev/null; then echo "API ready"; break; fi
  sleep 2
done

exec streamlit run dashboard/streamlit_app.py \
  --server.port "$PORT" --server.address 0.0.0.0 \
  --server.enableXsrfProtection false --server.enableCORS false \
  --browser.gatherUsageStats false
