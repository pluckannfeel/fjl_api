from typing import List
from pydantic import BaseModel, EmailStr
from typing import List


class VerificationEmail(BaseModel):
    email: List[EmailStr]

class EmailDetails(BaseModel):
    email: EmailStr
    subject: str
    body: str

