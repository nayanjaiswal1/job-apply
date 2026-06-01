from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, Integer, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(Text, primary_key=True)  # SHA-256(title+company+location)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    company: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str | None] = mapped_column(Text)
    platform: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    jd_text: Mapped[str | None] = mapped_column(Text)
    salary_range: Mapped[str | None] = mapped_column(Text)
    remote: Mapped[bool | None] = mapped_column(Boolean)
    exp_level: Mapped[str | None] = mapped_column(Text)
    match_score: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(Text, default="discovered")
    source_type: Mapped[str | None] = mapped_column(Text)
    posted_at: Mapped[datetime | None] = mapped_column()
    scraped_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str | None] = mapped_column(Text)
    funding_stage: Mapped[str | None] = mapped_column(Text)
    team_size: Mapped[str | None] = mapped_column(Text)
    tech_stack: Mapped[str | None] = mapped_column(Text)  # for SQL filters
    glassdoor_rating: Mapped[float | None] = mapped_column(Float)
    summary: Mapped[str | None] = mapped_column(Text)  # JSON CompanyProfile; authoritative
    researched_at: Mapped[datetime | None] = mapped_column()


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    job_id: Mapped[str | None] = mapped_column(Text, ForeignKey("jobs.id"))
    resume_version: Mapped[str | None] = mapped_column(Text)
    cover_letter: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column()
    status: Mapped[str] = mapped_column(Text, default="applied")
    last_reply: Mapped[str | None] = mapped_column(Text)
    last_reply_at: Mapped[datetime | None] = mapped_column()
    submit_screenshot: Mapped[str | None] = mapped_column(Text)


class Outreach(Base):
    __tablename__ = "outreach"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    job_id: Mapped[str | None] = mapped_column(Text, ForeignKey("jobs.id"))
    person: Mapped[str | None] = mapped_column(Text)
    company: Mapped[str | None] = mapped_column(Text)
    channel: Mapped[str | None] = mapped_column(Text)  # email | linkedin_dm
    message: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column()
    reply: Mapped[str | None] = mapped_column(Text)
    reply_at: Mapped[datetime | None] = mapped_column()


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[bytes] = mapped_column(nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str | None] = mapped_column(Text)
    model_answer: Mapped[str | None] = mapped_column(Text)
    user_answer: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[str | None] = mapped_column(Text)  # JSON array
    source_jds: Mapped[str | None] = mapped_column(Text)  # JSON array of job IDs
    confidence: Mapped[str] = mapped_column(Text, default="unseen")
    practice_count: Mapped[int] = mapped_column(Integer, default=0)
    last_practiced: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    filename: Mapped[str | None] = mapped_column(Text)
    sections: Mapped[str | None] = mapped_column(Text)  # JSON
    ats_score: Mapped[float | None] = mapped_column(Float)
    ai_detect_score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class UserProfile(Base):
    __tablename__ = "user_profile"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default="me")
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[str | None] = mapped_column(Text)
    linkedin_url: Mapped[str | None] = mapped_column(Text)
    github_url: Mapped[str | None] = mapped_column(Text)
    portfolio_url: Mapped[str | None] = mapped_column(Text)
    current_title: Mapped[str | None] = mapped_column(Text)
    current_company: Mapped[str | None] = mapped_column(Text)
    years_exp: Mapped[int | None] = mapped_column(Integer)
    notice_period: Mapped[str | None] = mapped_column(Text)
    current_location: Mapped[str | None] = mapped_column(Text)
    target_locations: Mapped[str | None] = mapped_column(Text)  # JSON array
    expected_salary: Mapped[int | None] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(Text, default="INR")
    onboarding_step: Mapped[int] = mapped_column(Integer, default=1)
    preferences: Mapped[str | None] = mapped_column(Text)  # JSON Preferences model
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    application_id: Mapped[str | None] = mapped_column(Text, ForeignKey("applications.id"))
    day_offset: Mapped[int | None] = mapped_column(Integer)  # 7 | 14 | 21
    channel: Mapped[str | None] = mapped_column(Text)  # email | linkedin_dm
    draft: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="draft")
    sent_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
