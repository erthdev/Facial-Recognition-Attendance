from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import (
    dashboard,
    students,
    attendance,
    reports
)


app = FastAPI(
    title="FaceTrack Attendance API",
    description="API for the Face-Based Attendance System",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(dashboard.router)
app.include_router(students.router)
app.include_router(attendance.router)
app.include_router(reports.router)


@app.get("/")
def root():
    return {
        "message": "FaceTrack API is running."
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "application": "FaceTrack Attendance System"
    }