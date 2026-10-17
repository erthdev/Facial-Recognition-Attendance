# Setup guide: Windows 10 / 11

[Back to the main page](README.md) | [Linux guide](README_Linux.md) | [macOS guide](README_macOS.md)

> These steps are the standard ones for Windows but have not been tested on a Windows machine yet. The project code is the same as on Linux. If something fails, check the Troubleshooting table at the bottom and open an issue.

Use **PowerShell** for all commands.

## Step 1. Prepare the computer
- Plug in the charger if you are on a laptop.
- Close browser tabs and other heavy apps.
- The dlib build takes 10 to 20 minutes and needs a few GB of free RAM.

## Step 2. Install the tools

dlib is C++ and is compiled during installation, so a compiler and CMake are needed.

1. **Python 3.12** from https://www.python.org/downloads/ . In the installer, tick **"Add python.exe to PATH"**.
2. **Visual Studio Build Tools 2022** from https://visualstudio.microsoft.com/visual-cpp-build-tools/ . In the installer choose the workload **"Desktop development with C++"**. This is a large download (several GB).
3. **CMake**: run `winget install Kitware.CMake`, or download it from https://cmake.org/download/ and tick "Add CMake to the PATH".
4. **Git** (optional, to clone the repository): `winget install Git.Git`.
5. **Close and reopen PowerShell**, then check:
```powershell
python --version
cmake --version
```

## Step 3. Check that the webcam works
- Open the **Camera** app and confirm you see yourself, then close it so it releases the camera.
- Settings > Privacy & security > Camera: turn on **Camera access** and **Let desktop apps access your camera**.

## Step 4. Get the project and create the virtual environment
```powershell
git clone <your-repository-url> face_attendance      # or extract face_attendance.zip into your user folder
cd face_attendance
python -m venv .venv
.venv\Scripts\Activate.ps1                           # run this in every new terminal
python -m pip install --upgrade pip
```
Your prompt should now start with `(.venv)`.

If PowerShell says running scripts is disabled, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, answer Y, and activate again. Alternatively use Command Prompt and `.venv\Scripts\activate.bat`.

## Step 5. Install the Python libraries (order matters)
```powershell
pip install "setuptools<81" wheel
pip install numpy opencv-python pandas streamlit pytest
pip install dlib
pip install face_recognition
```
`pip install dlib` compiles C++ and takes 10 to 20 minutes. Do not interrupt it. `setuptools<81` must come first because `face_recognition_models` still imports `pkg_resources`.

## Step 6. Verify the installation
```powershell
python -c "import face_recognition, cv2, streamlit, numpy; print('OK')"
```
It must print `OK`.

## Step 7. Run the automated tests
```powershell
pytest 04_Testing -v
```
All tests should pass.

## Step 8. Create the database
```powershell
python 01_Source_Code\db.py init       # creates 02_Data\attendance.db
```
Use `python 01_Source_Code\db.py reset` any time you want a fresh, empty database.

## Step 9. Start the app
```powershell
streamlit run 01_Source_Code\app.py
```
It opens at http://localhost:8501. Allow the camera when the browser asks. If Windows Firewall shows a prompt for Python, you can choose **Cancel**; the app only needs `localhost`.

Next: [Using the app](README.md#using-the-app) and [Tuning with your own data](README.md#tuning-with-your-own-data) on the main page.

## Step 10. Inspect the stored data

Windows does not ship the `sqlite3` command, so use Python's built-in module:
```powershell
python -c "import sqlite3; [print(r) for r in sqlite3.connect('02_Data/attendance.db').execute('SELECT * FROM attendance')]"
python -c "import sqlite3; [print(r) for r in sqlite3.connect('02_Data/attendance.db').execute('SELECT person_id, length(encoding) FROM face_encodings')]"
```
Every encoding length should be 1024. (Optional: install [DB Browser for SQLite](https://sqlitebrowser.org/) for a graphical view, and close it before using the app so the database is not locked.)

## Step 11 (optional). Launch it like a real app

Create `launch.bat` in the project folder:

```bat
@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
start "Face Attendance server" /min cmd /c "streamlit run 01_Source_Code\app.py --server.headless true"
timeout /t 6 >nul
start chrome --app=http://localhost:8501
```

Double-click it to start. For a desktop icon, right-click `launch.bat` > Show more options > Send to > Desktop (create shortcut). The server runs in a minimized window; close that window to stop the app. Use `start msedge --app=...` instead of `chrome` if you prefer Edge.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| "Microsoft Visual C++ 14.0 or greater is required" or "CMake must be installed" | Install the Build Tools workload **Desktop development with C++** and CMake (Step 2), reopen PowerShell, run `pip install dlib` again |
| `python` opens the Microsoft Store or is not found | Reinstall Python and tick "Add python.exe to PATH", or use `py -3.12 -m venv .venv` for Step 4 |
| `Activate.ps1 cannot be loaded` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or use Command Prompt with `.venv\Scripts\activate.bat` |
| `dlib` build fails for another reason | Close other apps, keep the charger in, make sure Step 2 finished fully, then retry. As a last resort, swap only `vision.py` to OpenCV YuNet + SFace |
| `No module named 'pkg_resources'` | `pip install "setuptools<81"` inside the venv |
| NumPy binary-compatibility error | `pip install "numpy<2"` then `pip install --force-reinstall opencv-python` |
| "Face recognition library is not installed correctly" | Run the Step 6 command to see the real error; details are also in `app.log` |
| Webcam not found or black picture | Check the camera privacy settings (Step 3) and close any other app using the camera (Teams, Zoom, Camera) |
| Browser shows no camera | Click the lock icon next to the URL > Site settings > Camera > Allow for localhost |
| Slow recognition | Lower `DETECT_SCALE`, close other apps, plug in the charger and use the High performance power mode |
| False matches | Lower `MATCH_THRESHOLD` toward 0.45 to 0.5; enroll more varied samples |
| Missed matches in another room | Enroll under similar lighting; add samples from several conditions |
| "Image quality too low" all the time | Add light in front of you, hold still, or lower `MIN_BLUR` / `MIN_BRIGHTNESS` a little |
| "database is locked" | Close other programs using the file (a DB viewer, or a second copy of the app) |
| "Database unavailable" | `02_Data\attendance.db` is missing or locked: run `python 01_Source_Code\db.py init` |
