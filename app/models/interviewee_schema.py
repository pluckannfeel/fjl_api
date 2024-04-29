from pydantic import BaseModel, EmailStr, HttpUrl, UUID4
from typing import List, Optional
from datetime import date, datetime


class InterviewDateTime(BaseModel):
    id: str
    date: str
    time: str


class Interviewee(BaseModel):
    id: UUID4
    img_url: HttpUrl
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    birth_date: date
    age: int
    gender: str
    nationality: str
    university_name: str
    selected_dates: List[InterviewDateTime]
    residence_card_number: str
    residence_card_expiry: date
    residence_card_image: HttpUrl
    phone_number: str
    email: EmailStr
    password_hash: Optional[str]
    is_verified: bool
    created_at: datetime
    updated_at: datetime
