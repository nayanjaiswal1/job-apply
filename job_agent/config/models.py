from pydantic import BaseModel, Field


class AgentModelConfig(BaseModel):
    primary: str
    fallback: str
    min_mode: str


class ModelConfig(BaseModel):
    orchestrator: AgentModelConfig
    resume_rewrite: AgentModelConfig
    cover_letter: AgentModelConfig
    job_scoring: AgentModelConfig
    company_research: AgentModelConfig
    referral_dm: AgentModelConfig
    mail_classifier: AgentModelConfig
    form_screening: AgentModelConfig
    interview_prep: AgentModelConfig


class ChromaConfig(BaseModel):
    job_embeddings_collection: str = Field(default="job_embeddings")
    question_embeddings_collection: str = Field(default="question_embeddings")


class ScheduleConfig(BaseModel):
    job_search_interval_hours: int = Field(default=6)
    linkedin_post_interval_hours: int = Field(default=4)
    mail_watcher_interval_minutes: int = Field(default=30)
    followup_time: str = Field(default="09:00")
    stale_check_time: str = Field(default="08:00")


class NotificationsConfig(BaseModel):
    telegram: bool = Field(default=False)
    email_digest: bool = Field(default=True)


class AppConfig(BaseModel):
    chroma: ChromaConfig = Field(default_factory=ChromaConfig)
    models: ModelConfig
    schedule: ScheduleConfig = Field(default_factory=ScheduleConfig)
    notifications: NotificationsConfig = Field(default_factory=NotificationsConfig)
