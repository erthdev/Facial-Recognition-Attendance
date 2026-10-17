# Setup guide: macOS (Apple Silicon or Intel)

[Back to the main page](README.md) | [Linux guide](README_Linux.md) | [Windows guide](README_Windows.md)

> These steps are the standard ones for macOS but have not been tested on a Mac yet. The project code is the same as on Linux. If something fails, check the Troubleshooting table at the bottom and open an issue.

Use the **Terminal** app for all commands.

## Step 1. Prepare the Mac
- Plug in the charger if you are on a laptop.
- Close browser tabs and other heavy apps.
- The dlib build takes a few to 20 minutes depending on the Mac and needs a few GB of free RAM.

## Step 2. Install the tools

dlib is C++ and is compiled during installation, so a compiler and CMake are needed.

```bash
xcode-select --install                 # compiler tools; a dialog appears, click Install
```
Install [Homebrew](https://brew.sh) if you do not have it (follow the one-line command on that page), then:
```bash
brew install cmake python@3.12
```
Check:
```bash
python3.12 --version
cmake --version
```

## Step 3. Check that the webcam works
- Open **Photo Booth** and confirm you see yourself, then close it so it releases the camera.
- The first time your browser asks to use the camera, click **Allow**. If you denied it earlier: System Settings > Privacy & Security > Camera, and turn it on for your browser.

## Step 4. Get the project and create the virtual environment
```bash
git clone <your-repository-url> face_attendance      # or: unzip face_attendance.zip -d ~/
cd ~/face_attendance
python3.12 -m venv .venv
source .venv/bin/activate                            # run this in every new terminal
python -m pip install --upgrade pip
```
Your prompt should now start with `(.venv)`. Inside the venv, `python` is the right one.

## Step 5. Install the Python libraries (order matters)
```bash
pip install "setuptools<81" wheel
pip install numpy opencv-python pandas streamlit pytest
pip install dlib                       # compiles C++. Do not interrupt it.
pip install face_recognition
```
`setuptools<81` must come first because `face_recognition_models` still imports `pkg_resources`.

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
It opens at http://localhost:8501. Allow the camera when the browser asks. Chrome is recommended; Safari should also work for camera capture.

Next: [Using the app](README.md#using-the-app) and [Tuning with your own data](README.md#tuning-with-your-own-data) on the main page.

## Step 10. Inspect the stored data

macOS includes the `sqlite3` command:
```bash
sqlite3 02_Data/attendance.db "SELECT * FROM attendance;"
sqlite3 02_Data/attendance.db "SELECT person_id, length(encoding) FROM face_encodings;"   # every row should be 1024
```

## Step 11 (optional). Launch it like a real app

Create `launch.command` in the project folder:

```bash
#!/usr/bin/env bash
cd "$(dirname "$0")"
source .venv/bin/activate
(sleep 5 && open -na "Google Chrome" --args --app=http://localhost:8501) &
streamlit run 01_Source_Code/app.py --server.headless true
```

Run `chmod +x launch.command` once, then double-click the file in Finder. It opens Terminal and an app-style Chrome window. Closing the Terminal window stops the app. You can drag the file to the Dock or make an alias on the Desktop. If macOS blocks it the first time, right-click the file > Open.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `xcrun: error` or "No CMAKE_CXX_COMPILER" | Run `xcode-select --install` and `brew install cmake`, then `pip install dlib` again |
| `python3.12: command not found` | `brew install python@3.12`, then open a new Terminal window. Any Python 3.10 or newer should also work: use `python3` instead |
| `dlib` build fails for another reason | Close other apps, make sure Step 2 finished fully, then retry. As a last resort, swap only `vision.py` to OpenCV YuNet + SFace |
| `No module named 'pkg_resources'` | `pip install "setuptools<81"` inside the venv |
| NumPy binary-compatibility error | `pip install "numpy<2"` then `pip install --force-reinstall opencv-python` |
| "Face recognition library is not installed correctly" | Run the Step 6 command to see the real error; details are also in `app.log` |
| Camera black or not found | System Settings > Privacy & Security > Camera: allow your browser. Close other apps using the camera (FaceTime, Zoom, Photo Booth) |
| Browser shows no camera | Click the lock icon next to the URL > Site settings > Camera > Allow for localhost |
| Slow recognition | Lower `DETECT_SCALE`, close other apps, plug in the charger |
| False matches | Lower `MATCH_THRESHOLD` toward 0.45 to 0.5; enroll more varied samples |
| Missed matches in another room | Enroll under similar lighting; add samples from several conditions |
| "Image quality too low" all the time | Add light in front of you, hold still, or lower `MIN_BLUR` / `MIN_BRIGHTNESS` a little |
| "database is locked" | Close other programs using the file (an open `sqlite3` shell or DB viewer) |
| "Database unavailable" | `02_Data/attendance.db` is missing or locked: run `python 01_Source_Code/db.py init` |
