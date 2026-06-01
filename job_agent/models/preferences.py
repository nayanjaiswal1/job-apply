from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Preferences(BaseModel):
    min_salary: int | None = None
    preferred_locations: list[str] = Field(default_factory=list)
    remote: Literal["remote", "hybrid", "onsite", "any"] = "any"
    role_levels: list[str] = Field(default_factory=list)
    target_roles: list[str] = Field(default_factory=list)
    blacklist_companies: list[str] = Field(default_factory=list)
    blacklist_keywords: list[str] = Field(default_factory=list)
    preferred_tech: list[str] = Field(default_factory=list)
    max_applications_per_day: int = 10
