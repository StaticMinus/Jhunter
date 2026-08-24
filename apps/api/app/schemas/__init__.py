"""
AI Job Hunter — Pydantic v2 Request and Response Schemas
"""

from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict, Field


# ─── Auth Schemas ───

class GoogleAuthRequest(BaseModel):
    credential: str = Field(..., description="Google ID Token / Authorization code")

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


# ─── User & Profile Schemas ───

class SkillItem(BaseModel):
    skill: str
    category: Optional[str] = "Technical"
    proficiency: Optional[str] = "Advanced"
    evidence: Optional[str] = None

class ExperienceItem(BaseModel):
    employer: str
    title: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    sector: Optional[str] = None

class EducationItem(BaseModel):
    institution: str
    qualification: str
    dates: Optional[str] = None
    field: Optional[str] = None

class CertificationItem(BaseModel):
    name: str
    issuer: str
    year: Optional[int] = None

class CandidateProfileBase(BaseModel):
    summary: Optional[str] = None
    seniority: Optional[str] = "Senior"
    location: Optional[str] = "Nigeria"
    salary_floor: Optional[float] = 500000.0
    preferences_json: Dict[str, Any] = Field(default_factory=dict)

class CandidateProfileUpdate(CandidateProfileBase):
    skills: Optional[List[SkillItem]] = None
    experiences: Optional[List[ExperienceItem]] = None
    education: Optional[List[EducationItem]] = None
    certifications: Optional[List[CertificationItem]] = None

class CandidateProfileResponse(CandidateProfileBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    version: int
    created_at: datetime
    updated_at: datetime
    skills: List[SkillItem] = []
    experiences: List[ExperienceItem] = []
    education: List[EducationItem] = []
    certifications: List[CertificationItem] = []

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    name: str
    timezone: str
    created_at: datetime
    profile: Optional[CandidateProfileResponse] = None


# ─── Job Schemas ───

class SalaryInfo(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    currency: Optional[str] = "NGN"

class JobCreate(BaseModel):
    source_id: Optional[str] = None
    external_id: Optional[str] = None
    canonical_url: str
    title: str
    employer: str
    location: Optional[str] = None
    work_mode: Optional[str] = "unknown"
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: Optional[str] = "NGN"
    description: str
    posted_at: Optional[datetime] = None

class JobFeatureResponse(BaseModel):
    skills_json: List[str] = []
    seniority: Optional[str] = None
    industry: Optional[str] = None
    visa_signal: str = "unknown"
    remote_signal: str = "unknown"
    extracted_salary: Optional[Dict[str, Any]] = None
    requirements_json: List[str] = []

class JobMatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    match_score: int
    opportunity_score: int
    explanation_json: Dict[str, Any]
    gaps_json: List[str]
    created_at: datetime

class JobDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    canonical_url: str
    title: str
    employer: str
    location: Optional[str]
    work_mode: Optional[str]
    salary_min: Optional[float]
    salary_max: Optional[float]
    currency: Optional[str]
    description: str
    posted_at: Optional[datetime]
    created_at: datetime
    features: Optional[JobFeatureResponse] = None
    match: Optional[JobMatchResponse] = None


# ─── Application & Document Schemas ───

class ApplicationAnswerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    question: str
    answer: str
    confidence: float
    reviewed: bool
    flagged_for_review: bool

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    type: str
    version: int
    content_markdown: str
    generated_at: datetime

class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    job_id: str
    profile_id: str
    status: str
    approval_state: str
    applied_at: Optional[datetime]
    method: Optional[str]
    created_at: datetime
    job: Optional[JobDetailResponse] = None
    documents: List[DocumentResponse] = []
    answers: List[ApplicationAnswerResponse] = []

class ApplicationPrepareRequest(BaseModel):
    custom_notes: Optional[str] = None

class ApplicationActionRequest(BaseModel):
    reason: Optional[str] = None


# ─── Integration & Notification Schemas ───

class GmailStatusResponse(BaseModel):
    connected: bool
    email: Optional[str] = None
    sync_active: bool = False
    applied_label_id: Optional[str] = None

class TelegramStatusResponse(BaseModel):
    connected: bool
    bot_username: Optional[str] = None
    chat_linked: bool = False

class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    channel: str
    type: str
    payload_json: Dict[str, Any]
    sent_at: datetime
    read_at: Optional[datetime]

class KPISummaryResponse(BaseModel):
    jobs_scanned: int
    new_jobs: int
    strong_matches: int
    high_opportunity: int
    pending_approval: int
    applied: int
    interview: int
    rejected: int
    response_rate_percent: float
