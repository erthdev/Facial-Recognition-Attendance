# Face-Based Attendance System

A webcam captures a face, `face_recognition` (dlib) turns it into a 128-number encoding, the app compares it with the encodings stored in SQLite, applies attendance rules (match threshold, duplicate window, Present/Late cutoff), saves the record, and shows reports with CSV export. Everything runs locally; no internet is needed after installation.

Built with Python 3.12, Streamlit, OpenCV, dlib / `face_recognition`, SQLite and pandas.

## Choose your setup guide

| Your system | Guide | Status |
| --- | --- | --- |
| Linux (Mint / Ubuntu) | [Linux setup guide](/07_os/README_Linux.md) | Developed and tested here |
| Windows 10 / 11 | [Windows setup guide](/07_os/README_Windows.md) | Standard steps, not yet tested |
| macOS (Apple Silicon or Intel) | [macOS setup guide](/07_os/README_macOS.md) | Standard steps, not yet tested |

The code is identical on all three systems. Only the installation steps differ (mainly how dlib gets compiled). Once the app is running, come back to this page for [Using the app](#using-the-app).

---

## Using the app

Start it from the project folder with the virtual environment active:

```bash
streamlit run 01_Source_Code/app.py
```

It opens at http://localhost:8501. Allow the camera when the browser asks (localhost is permitted).

### Enroll people (sidebar > Enroll)
1. Type the student number (e.g. `2023-00123`), full name and section.
2. Tick the **consent** checkbox (required).
3. Take a photo and press **Add this photo**. Repeat for **3 to 5 photos** with slightly different angles and expressions. Each photo is checked for brightness, blur and exactly one face; bad photos are rejected with a message.
4. Press **Enroll**. You should see "Enrolled <name> with N face samples."

Only the 128-number encodings are stored. Photos are processed in memory and discarded.

### Take attendance (sidebar > Attendance)
1. Confirm the **session label**, **class start** and **grace period** in *Session settings*.
2. Look at the camera, take a photo, press **Record attendance**.

| Result | Meaning |
| --- | --- |
| Welcome, Juan: Present | Recognized, on or before class start + grace |
| Welcome, Juan: Late | Recognized, after the cutoff |
| Already recorded at 09:02 for this session | Same person scanned again within the duplicate window; no new row |
| Face not recognized | Distance above the threshold; no record |

The page also shows the match distance and how many seconds the scan took.

### View reports (sidebar > Reports)
Pick a date, section and session. You get the Present / Late / Absent counts, the attendance table, the Absent list (enrolled minus scanned), a Present-vs-Late chart per day, and a **Download CSV** button (`attendance_YYYY-MM-DD.csv`).

### Delete someone's data
*Enroll > Enrolled people / Delete my data* removes a person, their face encodings and their attendance records.

---

## Tuning with your own data

Edit `01_Source_Code/config.py`, then restart the app.

| Setting | Default | What to do |
| --- | --- | --- |
| `MATCH_THRESHOLD` | 0.5 | False matches: go lower (0.45 to 0.5). Missed matches: go toward 0.6 |
| `CLASS_START`, `GRACE_MINUTES` | 09:00, 15 | Late cutoff = start + grace |
| `DUPLICATE_WINDOW_MIN` | 30 | Repeat-scan window per person per session |
| `MIN_BLUR` | 60 | Variance of the Laplacian; try 40 to 100 for your webcam |
| `MIN_BRIGHTNESS` | 50 | Mean gray level; raise it if dark photos get through |
| `DETECT_SCALE` | 0.5 | Smaller is faster; larger finds smaller or farther faces |

**Measuring accuracy:** enroll N people, run 10 scans each, then count correct matches, false rejections and false accepts at your chosen threshold. Note the match distances and the "Processed in X s" time shown on the Attendance page.

**Tips for a weak webcam:** light in front of you (never behind), enroll in the same room you will scan in, and add a few samples at different angles.

---

## Live demo checklist

1. Charger in, other apps closed, lighting tested in the demo room.
2. `python 01_Source_Code/db.py reset` for a fresh database, then start the app.
3. Enroll yourself and one classmate; show the consent box and multi-photo capture; show a rejected photo (hand over the lens, or two people).
4. Scan an enrolled person (Present), scan again (Duplicate).
5. Set *Class start* to a time in the past and scan (Late). Scan an unenrolled person (Unknown).
6. Open Reports: table, chart, Absent list, CSV download. Then show the stored rows (the setup guide for your system has the command).
7. Record a backup video and keep copies in `06_Demo_Backup/`, on a second drive and on a USB drive.

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
├── 02_Data/          schema.sql, generate_sample_images.py, sample_images/ (attendance.db is created locally)
├── 03_Documentation/ diagrams (redraw in draw.io to match the final code)
├── 04_Testing/       test_cases.md, bug_log.md, tests/ (pytest)
├── 05_Presentation/
├── 06_Demo_Backup/
├── README.md             (this page)
├── README_Linux.md
├── README_Windows.md
├── README_macOS.md
└── Contribution_Record.md
```

Run the automated tests any time with `pytest 04_Testing -v`. They use a throwaway database.

---

## Privacy and limitations

- Consent is required and its date is stored. Only encodings are stored, never photos.
- Biometric data is sensitive personal information under the Data Privacy Act of 2012 (RA 10173). Enroll only yourself and classmates who agreed.
- **Do not commit real data to GitHub.** Add these lines to `.gitignore` so the database (which holds face encodings of real people) and the log never get pushed:
  ```
  *.db
  app.log
  ```
  If `02_Data/attendance.db` was already committed, remove it from tracking with `git rm --cached 02_Data/attendance.db` and commit again. Anyone who clones the repo creates a fresh empty database with `python 01_Source_Code/db.py init`. Also avoid committing photos of real faces in `sample_images/`.
- **No liveness detection:** a printed photo or phone screen may fool it (test T12). This is a prototype, not an identity-verification product.
- For real deployment: encrypt the database, add an admin login, add liveness detection (blink or challenge-response), and consider a FAISS index for large populations.
