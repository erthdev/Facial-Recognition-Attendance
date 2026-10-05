# Face-Based Attendance System

A webcam captures a face, `face_recognition` (dlib) turns it into a 128-number encoding, my code compares it with the encodings stored in SQLite, applies attendance rules (match threshold, duplicate window, Present/Late cutoff), saves the record, and shows reports with CSV export. Everything runs locally; no internet is needed after installation.

Built for: Linux Mint 22 / Ubuntu 24.04, Python 3.12, dual-core laptop, USB UVC webcam, Chrome.

---

## Step-by-step guide

### Step 1. Prepare the laptop
- Plug in the **charger** (the dlib build is heavy and the battery is weak).
- Close Chrome tabs and other heavy apps. Put the laptop on a hard surface so the vents stay clear.

### Step 2. Install the system packages
```bash
sudo apt update
sudo apt install -y build-essential cmake python3-dev python3-venv \
    libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev \
    v4l-utils cheese sqlite3
```

### Step 3. Check that the webcam works (before touching any code)
```bash
ls /dev/video*                 # should list /dev/video0
v4l2-ctl --list-devices        # should show the USB2.0 HD UVC WebCam
groups                         # you should be in the 'video' group
cheese                         # visual test; close it afterwards so it releases the camera
```
Not in the `video` group? Run `sudo usermod -aG video $USER`, then log out and back in.

### Step 4. Put the project in your home folder and create the virtual environment
```bash
unzip face_attendance.zip -d ~/        # creates ~/face_attendance
cd ~/face_attendance
python3 -m venv .venv
source .venv/bin/activate              # run this in every new terminal
pip install --upgrade pip
```

### Step 5. Install the Python libraries (order matters on Python 3.12)
```bash
pip install "setuptools<81" wheel
pip install numpy opencv-python pandas streamlit pytest
pip install dlib                       # compiles C++: 10 to 20 minutes on an i3. Do not interrupt it.
pip install face_recognition
```
`setuptools<81` must come first: `face_recognition_models` still imports `pkg_resources`.

### Step 6. Verify the installation
```bash
python -c "import face_recognition, cv2, streamlit, numpy; print('OK')"
```
It must print `OK`. If not, see **Troubleshooting** below.

### Step 7. Run the automated tests
```bash
pytest 04_Testing -v
```
All tests should pass. They use a throwaway database, so your real data is never touched.

### Step 8. Create the database
```bash
python 01_Source_Code/db.py init       # creates 02_Data/attendance.db (already included, empty)
```
Use `python 01_Source_Code/db.py reset` any time you want a **fresh, empty** database (e.g. before the demo).

### Step 9. Start the app
```bash
streamlit run 01_Source_Code/app.py
```
It opens Chrome at http://localhost:8501. When Chrome asks, **Allow** the camera (localhost is permitted).

### Step 10. Enroll people (sidebar > Enroll)
1. Type the student number (e.g. `2023-00123`), full name and section.
2. Tick the **consent** checkbox (required).
3. Take a photo and press **Add this photo**. Repeat for **3 to 5 photos** with slightly different angles and expressions. Each photo is checked for brightness, blur and exactly one face; bad photos are rejected with a message.
4. Press **Enroll**. You should see "Enrolled <name> with N face samples."

Only the 128-number encodings are stored. Photos are processed in memory and discarded.

### Step 11. Take attendance (sidebar > Attendance)
1. Confirm the **session label**, **class start** and **grace period** in *Session settings*.
2. Look at the camera, take a photo, press **Record attendance**.
3. Possible results:

| Result | Meaning |
| --- | --- |
| Welcome, Juan: Present | Recognized, on or before class start + grace |
| Welcome, Juan: Late | Recognized, after the cutoff |
| Already recorded at 09:02 for this session | Same person scanned again within the duplicate window; no new row |
| Face not recognized | Distance above the threshold; no record |

The page also shows the match distance and how many seconds the scan took. **Write that time down**; the project document asks for a measured number.

### Step 12. View reports (sidebar > Reports)
Pick a date, section and session. You get the Present / Late / Absent counts, the attendance table, the Absent list (enrolled minus scanned), a Present-vs-Late chart per day, and a **Download CSV** button (`attendance_YYYY-MM-DD.csv`).

### Step 13. Inspect the stored data
```bash
sqlite3 02_Data/attendance.db "SELECT * FROM attendance;"
sqlite3 02_Data/attendance.db "SELECT person_id, length(encoding) FROM face_encodings;"   # every row should be 1024
```

### Step 14. Tune it with your own data
Edit `01_Source_Code/config.py`, then restart the app (Ctrl+C, run Step 9 again).

| Setting | Default | What to do |
| --- | --- | --- |
| `MATCH_THRESHOLD` | 0.5 | False matches: go lower. Missed matches: go toward 0.6 |
| `CLASS_START`, `GRACE_MINUTES` | 09:00, 15 | Late cutoff = start + grace |
| `DUPLICATE_WINDOW_MIN` | 30 | Repeat-scan window per person per session |
| `MIN_BLUR` | 60 | Variance of the Laplacian; try 50 to 100 for your webcam |
| `MIN_BRIGHTNESS` | 50 | Mean gray level; raise it if dark photos get through |
| `DETECT_SCALE` | 0.5 | Smaller is faster; larger finds smaller or farther faces |

**Measuring accuracy (for your defense):** enroll N people, run 10 scans each, then count correct matches, false rejections and false accepts at your chosen threshold. Log the distances shown on the Attendance page.

### Step 15. Prepare the live demo
1. Charger in, other apps closed, lighting tested in the demo room.
2. `python 01_Source_Code/db.py reset` for a fresh database, then start the app.
3. Enroll yourself and one classmate; show the consent box and multi-photo capture; show a rejected photo (hand over the lens, or two people).
4. Scan an enrolled person (Present), scan again (Duplicate).
5. Set *Class start* to a time in the past and scan (Late). Scan an unenrolled person (Unknown).
6. Open Reports: table, chart, Absent list, CSV download. Then run the `sqlite3` command from Step 13.
7. Record a backup video and copy it to `06_Demo_Backup/`, your second SSD and a USB drive.

---

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `dlib` build fails | Re-check Step 2 packages (`cmake`, `build-essential`, `python3-dev`), close other apps, keep the charger in. As a last resort, swap only `vision.py` to OpenCV YuNet + SFace |
| `No module named 'pkg_resources'` | `pip install "setuptools<81"` inside the venv |
| NumPy binary-compatibility error | `pip install "numpy<2"` then `pip install --force-reinstall opencv-python` |
| App says "Face recognition library is not installed correctly" | Run the Step 6 command to see the real error; details are also in `app.log` |
| Webcam not found | `ls /dev/video*`, check the `video` group, close Cheese or any app holding the camera |
| Chrome shows no camera | Click the lock icon next to the URL > Site settings > Camera > Allow for localhost |
| Slow recognition | Lower `DETECT_SCALE`, keep the HOG detector, close other apps, keep the laptop cool |
| False matches | Lower `MATCH_THRESHOLD` toward 0.5; enroll more varied samples |
| Missed matches in another room | Enroll under similar lighting; add samples from several conditions |
| "Image quality too low" all the time | Add light in front of you, hold still, or lower `MIN_BLUR` a little |
| "database is locked" | Close other programs using the file (e.g. an open `sqlite3` shell) |
| "Database unavailable" | `02_Data/attendance.db` is missing or locked: run `python 01_Source_Code/db.py init` |
| Streamlit reruns on every click | Normal behaviour; the app keeps its state in `st.session_state` |

---

## How it fits together

| File | Responsibility |
| --- | --- |
| `app.py`, `pages/` | UI: collects input, shows results and errors |
| `validation.py` | Image decodes, bright and sharp enough, exactly one face; form fields |
| `vision.py` | Detects faces, computes 128-d encodings, measures distances |
| `db.py` | The only module that runs SQL |
| `rules.py` | Match threshold, duplicate window, Present/Late |
| `reports.py` | pandas summaries, Absent list, CSV |
| `config.py` | All thresholds, paths and cutoff times |

```
face_attendance/
├── 01_Source_Code/   app.py, pages/, config.py, validation.py, vision.py, db.py, rules.py, reports.py, requirements.txt
├── 02_Data/          attendance.db, schema.sql, generate_sample_images.py, sample_images/
├── 03_Documentation/ diagrams (redraw in draw.io to match the final code)
├── 04_Testing/       test_cases.md, bug_log.md, tests/ (pytest)
├── 05_Presentation/
├── 06_Demo_Backup/
├── README.md
└── Contribution_Record.md
```

## Privacy and limitations
- Consent is required and its date is stored. Only encodings are stored, never photos. "Delete my data" is under *Enroll > Enrolled people*.
- Biometric data is sensitive personal information under the Data Privacy Act of 2012 (RA 10173). Enroll only yourself and classmates who agreed.
- **No liveness detection:** a printed photo or phone screen may fool it (test T12). This is a prototype, not an identity-verification product.
- For real deployment: encrypt the database, add an admin login, add liveness detection (blink or challenge-response), and consider a FAISS index for large populations.
