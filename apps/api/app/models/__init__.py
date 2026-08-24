"""
AI Job Hunter — SQLAlchemy Declarative Database Models
Covers the entire 14-page MVP Specification schema.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String, Text, Boolean, Integer, Numeric, DateTime,
    ForeignKey, func, JSON
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

# Fallback UUID type generator for SQLite / Postgres cross-compatibility
def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    google_tokens_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    profile: Mapped[Optional["CandidateProfile"]] = relationship("CandidateProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    seniority: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(128), default="Nigeria")
    salary_floor: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    preferences_json: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="profile")
    skills: Mapped[List["CandidateSkill"]] = relationship("CandidateSkill", back_populates="profile", cascade="all, delete-orphan")
    experiences: Mapped[List["Experience"]] = relationship("Experience", back_populates="profile", cascade="all, delete-orphan")
    education: Mapped[List["Education"]] = relationship("Education", back_populates="profile", cascade="all, delete-orphan")
    certifications: Mapped[List["Certification"]] = relationship("Certification", back_populates="profile", cascade="all, delete-orphan")
    matches: Mapped[List["JobMatch"]] = relationship("JobMatch", back_populates="profile", cascade="all, delete-orphan")
    applications: Mapped[List["Application"]] = relationship("Application", back_populates="profile", cascade="all, delete-orphan")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    skill: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    proficiency: Mapped[Optional[str]] = mapped_column(String(32), default="Advanced")
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="skills")


class Experience(Base):
    __tablename__ = "experiences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    employer: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sector: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="experiences")


class Education(Base):
    __tablename__ = "education"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    institution: Mapped[str] = mapped_column(String(255), nullable=False)
    qualification: Mapped[str] = mapped_column(String(255), nullable=False)
    dates: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    field: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="education")


class Certification(Base):
    __tablename__ = "certifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    issuer: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="certifications")


class JobSource(Base):
    __tablename__ = "job_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False) # scraper, api, rss, career_page
    base_url: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    jobs: Mapped[List["Job"]] = relationship("Job", back_populates="source")
    scan_runs: Mapped[List["ScanRun"]] = relationship("ScanRun", back_populates="source")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    source_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("job_sources.id", ondelete="SET NULL"), nullable=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    canonical_url: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    employer: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    work_mode: Mapped[Optional[str]] = mapped_column(String(32), default="unknown") # remote, hybrid, onsite, unknown
    salary_min: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    salary_max: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source: Mapped[Optional["JobSource"]] = relationship("JobSource", back_populates="jobs")
    features: Mapped[Optional["JobFeature"]] = relationship("JobFeature", back_populates="job", uselist=False, cascade="all, delete-orphan")
    matches: Mapped[List["JobMatch"]] = relationship("JobMatch", back_populates="job", cascade="all, delete-orphan")
    applications: Mapped[List["Application"]] = relationship("Application", back_populates="job", cascade="all, delete-orphan")


class JobFeature(Base):
    __tablename__ = "job_features"

    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)
    skills_json: Mapped[list] = mapped_column(JSON, default=list)
    seniority: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    visa_signal: Mapped[Optional[str]] = mapped_column(String(32), default="unknown") # indicated, possible, unknown, no_indication
    remote_signal: Mapped[Optional[str]] = mapped_column(String(32), default="unknown")
    extracted_salary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    requirements_json: Mapped[list] = mapped_column(JSON, default=list)
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job: Mapped["Job"] = relationship("Job", back_populates="features")


class JobMatch(Base):
    __tablename__ = "job_matches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    match_score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    opportunity_score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    explanation_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    gaps_json: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job: Mapped["Job"] = relationship("Job", back_populates="matches")
    profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="matches")


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT", index=True) # DRAFT, PENDING_APPROVAL, APPLIED, INTERVIEW, REJECTED, ARCHIVED
    approval_state: Mapped[str] = mapped_column(String(32), default="REVIEW") # AUTO, REVIEW, SKIP
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    method: Mapped[Optional[str]] = mapped_column(String(32), default="email") # email, web_form, manual
    external_reference: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    job: Mapped["Job"] = relationship("Job", back_populates="applications")
    profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="applications")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="application", cascade="all, delete-orphan")
    answers: Mapped[List["ApplicationAnswer"]] = relationship("ApplicationAnswer", back_populates="application", cascade="all, delete-orphan")
    communications: Mapped[List["Communication"]] = relationship("Communication", back_populates="application")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False) # tailored_cv, cover_letter, qa_sheet, briefing
    storage_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped["Application"] = relationship("Application", back_populates="documents")


class ApplicationAnswer(Base):
    __tablename__ = "application_answers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(3, 2), default=0.95)
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    flagged_for_review: Mapped[bool] = mapped_column(Boolean, default=False)

    application: Mapped["Application"] = relationship("Application", back_populates="answers")


class Communication(Base):
    __tablename__ = "communications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    application_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("applications.id", ondelete="SET NULL"), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(32), default="gmail")
    direction: Mapped[str] = mapped_column(String(16), default="inbound")
    message_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    body_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    classification: Mapped[Optional[str]] = mapped_column(String(64), nullable=True) # interview, assessment, rejection, shortlist

    application: Mapped[Optional["Application"]] = relationship("Application", back_populates="communications")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(32), default="telegram") # telegram, in_app, email
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="notifications")


class ScanRun(Base):
    __tablename__ = "scan_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    source_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("job_sources.id", ondelete="SET NULL"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="RUNNING")
    jobs_found: Mapped[int] = mapped_column(Integer, default=0)
    jobs_new: Mapped[int] = mapped_column(Integer, default=0)
    error_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    source: Mapped[Optional["JobSource"]] = relationship("JobSource", back_populates="scan_runs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
