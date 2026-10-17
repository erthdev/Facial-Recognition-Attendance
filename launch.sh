#!/usr/bin/env bash
# Starts the attendance server, opens it in an app-style window, stops the server on close.
cd "$(dirname "$(readlink -f "$0")")" || exit 1
source .venv/bin/activate
PORT=8501

if ! ss -ltn | grep -q ":$PORT "; then
  streamlit run 01_Source_Code/app.py --server.headless true --server.port $PORT \
      --browser.gatherUsageStats false > /tmp/face_attendance.log 2>&1 &
  SERVER_PID=$!
  trap '[ -n "$SERVER_PID" ] && kill $SERVER_PID 2>/dev/null' EXIT
fi

# wait up to 30 s for the server to answer
for _ in $(seq 1 30); do
  curl -s "http://localhost:$PORT" > /dev/null && break
  sleep 1
done

# separate profile so this window runs as its own process and the script knows when you close it
google-chrome --app="http://localhost:$PORT" --window-size=1000,720 \
    --user-data-dir="$HOME/.face_attendance_chrome"
