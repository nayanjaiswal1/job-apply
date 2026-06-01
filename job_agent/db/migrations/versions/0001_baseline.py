"""baseline

Revision ID: 0001
Revises:
Create Date: 2026-06-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("company", sa.Text, nullable=False),
        sa.Column("location", sa.Text),
        sa.Column("platform", sa.Text),
        sa.Column("url", sa.Text),
        sa.Column("jd_text", sa.Text),
        sa.Column("salary_range", sa.Text),
        sa.Column("remote", sa.Boolean),
        sa.Column("exp_level", sa.Text),
        sa.Column("match_score", sa.Float),
        sa.Column("status", sa.Text, server_default="discovered"),
        sa.Column("source_type", sa.Text),
        sa.Column("posted_at", sa.DateTime(timezone=True)),
        sa.Column("scraped_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "companies",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("name", sa.Text),
        sa.Column("funding_stage", sa.Text),
        sa.Column("team_size", sa.Text),
        sa.Column("tech_stack", sa.Text),
        sa.Column("glassdoor_rating", sa.Float),
        sa.Column("summary", sa.Text),
        sa.Column("researched_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "applications",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("job_id", sa.Text, sa.ForeignKey("jobs.id")),
        sa.Column("resume_version", sa.Text),
        sa.Column("cover_letter", sa.Text),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.Text, server_default="applied"),
        sa.Column("last_reply", sa.Text),
        sa.Column("last_reply_at", sa.DateTime(timezone=True)),
        sa.Column("submit_screenshot", sa.Text),
    )

    op.create_table(
        "outreach",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("job_id", sa.Text, sa.ForeignKey("jobs.id")),
        sa.Column("person", sa.Text),
        sa.Column("company", sa.Text),
        sa.Column("channel", sa.Text),
        sa.Column("message", sa.Text),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("reply", sa.Text),
        sa.Column("reply_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "questions",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("embedding", sa.LargeBinary, nullable=False),
        sa.Column("category", sa.Text, nullable=False),
        sa.Column("difficulty", sa.Text),
        sa.Column("model_answer", sa.Text),
        sa.Column("user_answer", sa.Text),
        sa.Column("tags", sa.Text),
        sa.Column("source_jds", sa.Text),
        sa.Column("confidence", sa.Text, server_default="unseen"),
        sa.Column("practice_count", sa.Integer, server_default="0"),
        sa.Column("last_practiced", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "resume_versions",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("filename", sa.Text),
        sa.Column("sections", sa.Text),
        sa.Column("ats_score", sa.Float),
        sa.Column("ai_detect_score", sa.Float),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "user_profile",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("full_name", sa.Text, nullable=False),
        sa.Column("email", sa.Text, nullable=False),
        sa.Column("phone", sa.Text),
        sa.Column("linkedin_url", sa.Text),
        sa.Column("github_url", sa.Text),
        sa.Column("portfolio_url", sa.Text),
        sa.Column("current_title", sa.Text),
        sa.Column("current_company", sa.Text),
        sa.Column("years_exp", sa.Integer),
        sa.Column("notice_period", sa.Text),
        sa.Column("current_location", sa.Text),
        sa.Column("target_locations", sa.Text),
        sa.Column("expected_salary", sa.Integer),
        sa.Column("currency", sa.Text, server_default="INR"),
        sa.Column("onboarding_step", sa.Integer, server_default="1"),
        sa.Column("preferences", sa.Text),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "follow_ups",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("application_id", sa.Text, sa.ForeignKey("applications.id")),
        sa.Column("day_offset", sa.Integer),
        sa.Column("channel", sa.Text),
        sa.Column("draft", sa.Text),
        sa.Column("status", sa.Text, server_default="draft"),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("follow_ups")
    op.drop_table("user_profile")
    op.drop_table("resume_versions")
    op.drop_table("questions")
    op.drop_table("outreach")
    op.drop_table("applications")
    op.drop_table("companies")
    op.drop_table("jobs")
