from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class StudentCreate(BaseModel):
    student_id: str = Field(min_length=1)
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)

    section: Optional[str] = None

    consent_given: bool
    consent_date: Optional[date] = None


class StudentResponse(BaseModel):
    person_id: int
    student_id: str
    full_name: str
    section: Optional[str] = None
    consent_given: bool
    consent_date: str
    biometric_enrolled: bool = False