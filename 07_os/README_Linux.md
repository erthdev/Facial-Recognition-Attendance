# Setup guide: Linux (Mint / Ubuntu 24.04)

[Back to the main page](README.md) | [Windows guide](README_Windows.md) | [macOS guide](README_macOS.md)

Tested on Linux Mint 22 (Ubuntu 24.04 base), Python 3.12, a dual-core laptop and a USB UVC webcam.

## Step 1. Prepare the laptop
- Plug in the **charger** (the dlib build is heavy).
- Close browser tabs and other heavy apps. Put the laptop on a hard surface so the vents stay clear.
- The dlib build takes 10 to 20 minutes on a dual-core CPU and needs a few GB of free RAM.

## Step 2. Install the system packages
```bash
sudo apt update
sudo apt install -y build-essential cmake python3-dev python3-venv \
    libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev \
    v4l-utils cheese sqlite3
```

## Step 3. Check that the webcam works (before touching any code)
```bash
ls /dev/video*                 # should list /dev/video0
v4l2-ctl --list-devices        # should show your webcam
groups                         # check whether you are in the 'video' group
cheese                         # visual test; close it afterwards so it releases the camera
```
If Cheese shows your face, you are fine. If the camera does not work and you are not in the `video` group, run `sudo usermod -aG video $USER`, then log out and back in.

## Step 4. Get the project and create the virtual environment
```bash
git clone <your-repository-url> face_attendance      # or: unzip face_attendance.zip -d ~/
cd ~/face_attendance
python3 -m venv .venv
source .venv/bin/activate                            # run this in every new terminal
python -m pip install --upgrade pip
```
Your prompt should now start with `(.venv)`.

## Step 5. Install the Python libraries (order matters)
```bash
pip install "setuptools<81" wheel
pip install numpy opencv-python pandas streamlit pytest
pip install dlib                       # compiles C++: 10 to 20 minutes. Do not interrupt it.
pip install face_recognition
```
`setuptools<81` must come first: `face_recognition_models` still imports `pkg_resources`.

While dlib compiles, the terminal shows only a spinner. To confirm it is working, run `top` in a second terminal and look for `cc1plus` (compiling) or `lto1-ltrans` / `ld` (final linking).

## Step 6. Verify the installation
```bash
python -c "import face_recognition, cv2, streamlit, numpy; print('OK')"
```
It must print `OK`.

## Step 7. Run the automated tests
```bash
pytest 04_Testing -v
```
All tests should pass.

## Step 8. Create the database
```bash
python 01_Source_Code/db.py init       # creates 02_Data/attendance.db
```
Use `python 01_Source_Code/db.py reset` any time you want a fresh, empty database.

## Step 9. Start the app
```bash
streamlit run 01_Source_Code/app.py
```
It opens at http://localhost:8501. Allow the camera when the browser asks.

Next: [Using the app](README.md#using-the-app) and [Tuning with your own data](README.md#tuning-with-your-own-data) on the main page.

## Step 10. Inspect the stored data
```bash
sqlite3 02_Data/attendance.db "SELECT * FROM attendance;"
sqlite3 02_Data/attendance.db "SELECT person_id, length(encoding) FROM face_encodings;"   # every row should be 1024
```

## Step 11 (optional). Launch it like a real app

This opens the app in its own window (no tabs or address bar) from your app menu. Create `launch.sh` in the project folder:

```bash
#!/usr/bin/env bash
cd "$(dirname "$(readlink -f "$0")")" || exit 1
source .venv/bin/activate
PORT=8501

if ! ss -ltn | grep -q ":$PORT "; then
  streamlit run 01_Source_Code/app.py --server.headless true --server.port $PORT \
      --browser.gatherUsageStats false > /tmp/face_attendance.log 2>&1 &
  SERVER_PID=$!
  trap '[ -n "$SERVER_PID" ] && kill $SERVER_PID 2>/dev/null' EXIT
fi

for _ in $(seq 1 30); do
  curl -s "http://localhost:$PORT" > /dev/null && break
  sleep 1
done

google-chrome --app="http://localhost:$PORT" --window-size=1000,720 \
    --user-data-dir="$HOME/.face_attendance_chrome"
```

Make it executable with `chmod +x launch.sh` and test it with `./launch.sh`. Chrome asks for camera permission once in this window; click Allow. Closing the window stops the server.

To add it to the app menu, create `~/.local/share/applications/face-attendance.desktop`:

```ini
[Desktop Entry]
Type=Application
Name=Face Attendance
Comment=Face-based attendance system
Exec=/home/YOUR_USER/face_attendance/launch.sh
Icon=camera-web
Terminal=false
Categories=Education;
```

Replace `YOUR_USER`, then run `update-desktop-database ~/.local/share/applications`. To use your own icon, set `Icon=` to the full path of a PNG.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `dlib` build fails | Re-check Step 2 (`cmake`, `build-essential`, `python3-dev`), close other apps, keep the charger in. If the terminal prints `Killed`, it ran out of memory: close apps and retry |
| `No module named 'pkg_resources'` | `pip install "setuptools<81"` inside the venv |
| NumPy binary-compatibility error | `pip install "numpy<2"` then `pip install --force-reinstall opencv-python` |
| "Face recognition library is not installed correctly" | Run the Step 6 command to see the real error; details are also in `app.log` |
| Webcam not found | `ls /dev/video*`, check the `video` group, close Cheese or any app holding the camera |
| Browser shows no camera | Click the lock icon next to the URL > Site settings > Camera > Allow for localhost |
| Slow recognition | Lower `DETECT_SCALE`, close other apps, keep the laptop cool and plugged in |
| False matches | Lower `MATCH_THRESHOLD` toward 0.45 to 0.5; enroll more varied samples |
| Missed matches in another room | Enroll under similar lighting; add samples from several conditions |
| "Image quality too low" all the time | Add light in front of you, hold still, or lower `MIN_BLUR` / `MIN_BRIGHTNESS` a little |
| "database is locked" | Close other programs using the file (an open `sqlite3` shell or DB viewer) |
| "Database unavailable" | `02_Data/attendance.db` is missing or locked: run `python 01_Source_Code/db.py init` |
| Launcher window is blank or does not start | Read `/tmp/face_attendance.log`; check `which google-chrome` and change the command in `launch.sh` if needed |
