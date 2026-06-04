from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class IndustryStat(BaseModel):
    source: str = "KOSIS"
    org_id: str
    tbl_id: str
    year: int
    region_code: str
    region_name: str
    industry_code: str
    industry_name: str
    industry_level: str
    indicator: str
    unit: str
    value: float | None
    last_modified: str | None = None
    quality_flag: str = "valid"
    raw: dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    is_valid: bool
    year: int | None = None
    region: str | None = None
    national_region: str | None = None
    indicator: str | None = None
    unit: str | None = None
    industry_level: str | None = None
    row_count: int = 0
    excluded_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

