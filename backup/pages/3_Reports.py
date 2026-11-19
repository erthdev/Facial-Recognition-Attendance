from datetime import date

import streamlit as st

import db
import reports

st.set_page_config(page_title="Reports", layout="centered")
st.title("Reports")

try:
    persons = db.list_persons()
    chosen_date = st.date_input("Date", value=date.today()).isoformat()
    section = st.selectbox("Section", ["All"] + db.list_sections())
    section = None if section == "All" else section
    session = st.selectbox("Session", ["All"] + db.list_sessions(chosen_date))
    session = None if session == "All" else session
    att = reports.get_attendance(date=chosen_date, section=section, session=session)
    att_all = reports.get_attendance(section=section)
except db.DatabaseError:
    st.error("Database unavailable. Try again.")
    st.stop()

if att.empty:
    st.info("No attendance records for this date.")
    st.stop()

counts = reports.summary(att, persons, section)
cols = st.columns(4)
for col, (label, value) in zip(cols, counts.items()):
    col.metric(label, value)

st.subheader("Attendance")
st.dataframe(att.drop(columns="attendance_id"), hide_index=True)

st.subheader("Absent")
absent = reports.absent_list(att, persons, section)
if absent.empty:
    st.write("Everyone enrolled has a record.")
else:
    st.dataframe(absent, hide_index=True)

st.subheader("Present vs Late per day")
st.bar_chart(reports.daily_counts(att_all))

st.download_button("Download CSV", reports.to_csv_bytes(att),
                   file_name=reports.csv_filename(chosen_date), mime="text/csv")
