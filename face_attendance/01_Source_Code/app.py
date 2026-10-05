"""Home page. Run from the project root:  streamlit run 01_Source_Code/app.py"""
import streamlit as st

import config
import db

st.set_page_config(page_title="Face Attendance", layout="centered")
st.title("Face-Based Attendance System")
st.caption("Webcam > face encoding > rules > SQLite > reports. Everything runs locally.")

try:
    db.init_db()
    persons = db.list_persons()
    records = db.fetch_attendance()
except db.DatabaseError:
    st.error("Database unavailable. Try again.")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Enrolled people", len(persons))
c2.metric("Attendance records", len(records))
c3.metric("Match threshold", config.MATCH_THRESHOLD)

st.markdown(
    """
**How to use** (pages are in the sidebar)
1. **Enroll**: enter details, tick consent, capture 3 to 5 photos.
2. **Attendance**: confirm the session label, capture a photo, press *Record attendance*.
3. **Reports**: filter by date, section or session; view Absent; download the CSV.
"""
)
st.caption(
    f"Present until {config.CLASS_START.strftime('%H:%M')} + {config.GRACE_MINUTES} min grace, "
    f"then Late. Duplicate window: {config.DUPLICATE_WINDOW_MIN} min. Edit `config.py` to change."
)
