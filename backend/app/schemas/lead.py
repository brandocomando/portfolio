"""Recruiter Lead Schemas."""

from typing import Optional
from pydantic import BaseModel, Field


class RecruiterLead(BaseModel):
    uid: str
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    provider: Optional[str] = None
    company_guess: Optional[str] = None
    first_seen: str
    last_seen: str
    total_questions_asked: int = 1
    last_question: str
