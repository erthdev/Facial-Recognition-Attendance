import streamlit as st

import config
import db
import validation
import vision

log = config.get_logger("enroll")
st.set_page_config(page_title="Enroll", layout="centered")
st.title("Enroll")

ss = st.session_state
ss.setdefault("samples", [])    # validated 128-d encodings captured so far
ss.setdefault("cam_n", 0)       # changing the camera widget key resets it
ss.setdefault("form_n", 0)      # changing the field keys clears the form

if ss.get("flash"):
    st.success(ss.pop("flash"))

n = ss.form_n
student_no = st.text_input("Student number", key=f"sno_{n}", placeholder="e.g. 2023-00123")
full_name = st.text_input("Full name", key=f"name_{n}")
section = st.text_input("Section", key=f"sec_{n}")
consent = st.checkbox(
    "I consent to my face encoding (not my photo) being stored for attendance.", key=f"consent_{n}"
)

st.subheader(f"Face samples: {len(ss.samples)} / {config.MAX_SAMPLES}")
st.caption(f"Capture {config.MIN_SAMPLES} to {config.MAX_SAMPLES} photos with slightly different angles and expressions.")
photo = st.camera_input("Take a photo", key=f"cam_{ss.cam_n}")

if photo is None:
    st.info("Waiting for the camera. If nothing appears: Camera not accessible. "
            "Check the connection and browser permission.")
elif st.button("Add this photo"):
    if len(ss.samples) >= config.MAX_SAMPLES:
        st.warning(f"You already have {config.MAX_SAMPLES} samples.")
    else:
        try:
            rgb, location = validation.validate_image(photo.getvalue())
            encoding = vision.encode_face(rgb, location)
        except validation.ValidationError as exc:
            st.error(str(exc))
        except vision.VisionUnavailableError as exc:
            st.error(str(exc))
        except ValueError as exc:
            log.error("Encoding failed: %s", exc)
            st.error("No face found. Face the camera directly.")
        else:
            ss.samples.append(encoding)
            ss.cam_n += 1
            st.rerun()

col_a, col_b = st.columns(2)
if col_b.button("Clear photos"):
    ss.samples = []
    ss.cam_n += 1
    st.rerun()

if col_a.button("Enroll", type="primary"):
    errors = validation.validate_enrollment_form(student_no, full_name, consent)
    if len(ss.samples) < config.MIN_SAMPLES:
        errors.append(f"Add at least {config.MIN_SAMPLES} valid photos ({len(ss.samples)} so far).")
    if not errors:
        try:
            if db.student_exists(student_no.strip()):
                errors.append("This student number is already enrolled.")
            else:
                db.add_person(student_no.strip(), full_name.strip(), section.strip(), consent, ss.samples)
                ss.flash = f"Enrolled {full_name.strip()} with {len(ss.samples)} face samples."
                ss.samples = []
                ss.cam_n += 1
                ss.form_n += 1
                st.rerun()
        except db.DuplicateStudentError:
            errors.append("This student number is already enrolled.")
        except db.DatabaseError:
            errors.append("Database unavailable. Try again.")
    for message in errors:
        st.error(message)

with st.expander("Enrolled people / Delete my data"):
    try:
        people = db.list_persons()
    except db.DatabaseError:
        people = None
        st.error("Database unavailable. Try again.")
    if people is not None:
        if people.empty:
            st.write("Nobody enrolled yet.")
        else:
            st.dataframe(people.drop(columns="person_id"), hide_index=True)
            labels = {f"{r.full_name} ({r.student_no})": int(r.person_id) for r in people.itertuples()}
            choice = st.selectbox("Person", list(labels))
            sure = st.checkbox("Permanently delete this person, their face data and attendance records.")
            if st.button("Delete", disabled=not sure):
                try:
                    db.delete_person(labels[choice])
                    ss.flash = f"Deleted all data for {choice}."
                    st.rerun()
                except db.DatabaseError:
                    st.error("Database unavailable. Try again.")
