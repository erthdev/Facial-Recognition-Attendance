# FaceTrack — 09_API

A separate FastAPI service for the vanilla HTML/CSS/JavaScript frontend.

## Project placement

Keep this folder beside your existing project folders:

```text
Facial-Recognition-Attendance/
├── 01_Source_Code/
├── 02_Data/
│   └── attendance.db
├── 08_Frontend/
└── 09_API/
    ├── main.py
    ├── config.py
    ├── database.py
    ├── schemas.py
    ├── routers/
    └── requirements.txt
```

The API defaults to `02_Data/attendance.db`. It opens the existing SQLite file and
does not initialize, migrate, delete, or recreate database tables.

## 1. Install dependencies

From the project root, activate the same virtual environment you use for Python:

```bash
source .venv/bin/activate
```

If your environment folder has a different name, activate that one instead. Then:

```bash
python -m pip install -r 09_API/requirements.txt
```

## 2. Start the API

Run this from the project root:

```bash
python -m uvicorn main:app --app-dir 09_API --reload --host 127.0.0.1 --port 8000
```

Open:
- API health: http://127.0.0.1:8000/api/health
- Interactive API docs: http://127.0.0.1:8000/docs

## 3. Connect the frontend

The JS starter already targets:

```javascript
http://127.0.0.1:8000/api
```

If you changed the API host or port, set `window.FACETRACK_API_BASE_URL`
before loading `js/api.js`.

Serve `08_Frontend` using VS Code Live Server (or another local HTTP server).
Do not open the HTML file directly with `file://`.

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | API and database connectivity |
| GET | `/api/dashboard` | Dashboard totals |
| GET | `/api/students` | List people |
| POST | `/api/students` | Add a basic person record, if schema mapping matches |
| GET | `/api/attendance` | List attendance records |
| GET | `/api/reports` | Return attendance rows for reporting |

## Important integration notes

- The known database tables are `persons`, `face_encodings`, and `attendance`, but
  the exact column definitions have not been verified in this starter.
- `GET` routes inspect the existing database and return rows without changing it.
- `POST /api/students` uses conservative column-name aliases. If your `persons`
  schema differs, it returns a clear error instead of guessing.
- Attendance writes are intentionally disabled until the exact `attendance`
  schema and business rules are mapped.
- This starter does not perform face detection, face matching, or biometric
  enrollment. It does not replace or modify your original Streamlit application.
- Before enabling write operations, back up `02_Data/attendance.db` and verify
  the actual table schema.

To inspect the schema safely using SQLite:

```bash
sqlite3 02_Data/attendance.db
```

Then at the SQLite prompt:

```sql
.schema persons
.schema attendance
.schema face_encodings
.quit
```

Share those `.schema` outputs to tailor the API precisely to your database.
