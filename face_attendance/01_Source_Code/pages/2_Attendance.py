import time
from datetime import date, datetime

import streamlit as st

import config
import db
import rules
import validation
import vision

log = config.get_logger("attendance_page")
st.set_page_config(page_title="Attendance", layout="centered")
st.title("Attendance")

with st.expander("Session settings", expanded=True):
    session_label = st.text_input("Session label", value=f"IPT-Lecture-{date.today().isoformat()}")
    class_start = st.time_input("Class start", value=config.CLASS_START, step=300)
    grace = st.number_input("Grace period (minutes)", 0, 120, config.GRACE_MINUTES)
    st.caption("For the demo: set the class start to a time in the past to see a Late result.")

photo = st.camera_input("Look at the camera", key="att_cam")
if photo is None:
    st.info("Waiting for the camera. If nothing appears: Camera not accessible. "
            "Check the connection and browser permission.")

if photo is not None and st.button("Record attendance", type="primary"):
    if not session_label.strip():
        st.error("Session label is required.")
        st.stop()
    started = time.perf_counter()
    try:
        rgb, location = validation.validate_image(photo.getvalue())
        encoding = vision.encode_face(rgb, location)
        person_id, distance = vision.best_match(encoding, db.load_all_encodings())
        now = datetime.now()
        last = db.last_scan(person_id, session_label.strip()) if person_id is not None else None
        decision = rules.decide(person_id, distance, last, now, class_start, int(grace))

        if decision.outcome in ("Present", "Late"):
            db.add_attendance(person_id, now.isoformat(timespec="seconds"),
                              decision.outcome, distance, session_label.strip())
        person = db.get_person(decision.person_id) if decision.person_id is not None else None
    except validation.ValidationError as exc:
        st.error(str(exc))
    except vision.VisionUnavailableError as exc:
        st.error(str(exc))
    except ValueError as exc:
        log.error("Encoding failed: %s", exc)
        st.error("No face found. Face the camera directly.")
    except db.DatabaseError:
        st.error("Database unavailable. Try again.")
    else:
        first = person["full_name"].split()[0] if person else ""
        if decision.outcome == "Present":
            st.success(f"Welcome, {first}: Present ({now:%H:%M})")
        elif decision.outcome == "Late":
            st.warning(f"Welcome, {first}: Late ({now:%H:%M})")
        elif decision.outcome == "Duplicate":
            st.info(f"Already recorded at {decision.previous_scan:%H:%M} for this session.")
        else:
            st.error("Face not recognized. Please enroll first or try again.")
        elapsed = time.perf_counter() - started
        st.caption(f"Match distance: {distance:.3f} (threshold {config.MATCH_THRESHOLD}). "
                   f"Processed in {elapsed:.2f} s.")
        log.info("scan outcome=%s person_id=%s distance=%.3f time=%.2fs",
                 decision.outcome, decision.person_id, distance, elapsed)
