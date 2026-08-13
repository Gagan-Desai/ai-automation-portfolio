
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, field_validator
from dateutil import parser as dateparser

class JobApplication(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_name: str
    email: str
    phone: str
    position_applied_for: str
    years_of_experience: float
    education: List[str]
    skills: List[str]
    availability_date: str

    @field_validator("availability_date")
    @classmethod
    def normalize_date(cls, v: str) -> str:
        return dateparser.parse(v).strftime("%Y-%m-%d")


class RecommendationStrength(str, Enum):
    strong = "strong"
    moderate = "moderate"
    weak = "weak"

class ReferenceLetter(BaseModel):
    model_config = ConfigDict(extra="forbid")
    referee_name: str
    referee_title: str
    referee_company: str
    candidate_name: str
    relationship_duration: str
    recommendation_strength: RecommendationStrength
    key_strengths: List[str]


class AcceptanceStatus(str, Enum):
    accepted = "accepted"
    declined = "declined"
    pending = "pending"

class OfferAcceptance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_name: str
    position: str
    start_date: str
    salary_offered: float
    acceptance_status: AcceptanceStatus
    signed_date: Optional[str] = None

    @field_validator("salary_offered", mode="before")
    @classmethod
    def parse_currency(cls, v):
        if isinstance(v, str):
            return float(v.replace("$", "").replace(",", "").strip())
        return v

    @field_validator("start_date", "signed_date")
    @classmethod
    def normalize_date(cls, v):
        if v is None:
            return v
        return dateparser.parse(v).strftime("%Y-%m-%d")