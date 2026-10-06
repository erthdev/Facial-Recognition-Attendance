# Creating the launch script.

-------------------------------------------------------------------------------------------
cat > launch.sh <<'EOF'
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
EOF
chmod +x launch.sh

-------------------------------------------------------------------------------------------

# Test it with ./launch.sh. A window should open with your app. Chrome will ask for camera permission once in this new profile. Click Allow, and it remembers. When you close the window, the server stops too.


# Adding the application menu:

-------------------------------------------------------------------------------------------
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/face-attendance.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Face Attendance
Comment=Face-based attendance system
Exec=$HOME/face_attendance/launch.sh
Icon=camera-web
Terminal=false
Categories=Education;
EOF
update-desktop-database ~/.local/share/applications
-------------------------------------------------------------------------------------------

# Open the Mint menu and search for "Face Attendance". You can right-click it to Add to panel or Add to desktop. I used camera-web (a built-in system icon) as a placeholder. To use your own, save a 256x256 PNG in the project folder and change the Icon= line to its full path, for example Icon=/home/herthtle/face_attendance/icon.png. You may also change the "Name" variable's value to change the application name.'

