# Face-Based Attendance System

A webcam captures a face, `face_recognition` (dlib) turns it into a 128-number encoding, the app compares it with the encodings stored in SQLite, applies attendance rules (match threshold, duplicate window, Present/Late cutoff), saves the record, and shows reports with CSV export. Everything runs locally; no internet is needed after installation.

# Note: This project is currently in development and I plan to finish and polish this project to it's utmost peak before publishing.