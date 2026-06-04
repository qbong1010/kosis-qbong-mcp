from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from .classifier import classify_industries
from .data_gate import check_gangneung_lq_requirements, local_lq_frame
from .growth import calculate_growth_rate
from .lq import calculate_lq
from .national_survey import normalize_national_business_survey
from .validators import validate_lq_inputs


@dataclass(frozen=True)
class VerifiedLqResult:
    status: str
    gate: dict[str, Any]
    results: list[dict[str, Any]]
    validation: dict[str, Any] | None = None


def run_verified_gangneung_lq(
    *,
    analysis_year: int = 2024,
    indicator: str = "employees",
    growth_start_year: int | None = None,
) -> VerifiedLqResult:
    gate = check_gangneung_lq_requirements(
        analysis_year=analysis_year,
        indicators=[indicator],
        growth_start_year=growth_start_year,
    )
    if not gate.is_ready:
        return VerifiedLqResult(status="blocked", gate=gate.to_dict(), results=[])

    local_df = local_lq_frame(analysis_year, indicator)
    national_df = normalize_national_business_survey(analysis_year)
    national_df = national_df[national_df["indicator"] == indicator].copy()
    validation = validate_lq_inputs(local_df, national_df)
    if not validation.is_valid:
        return VerifiedLqResult(status="blocked", gate=gate.to_dict(), results=[], validation=validation.model_dump())

    lq_df = calculate_lq(local_df, national_df)
    if growth_start_year is not None:
        local_start = local_lq_frame(growth_start_year, indicator)
        growth_source = pd.concat([local_start, local_df], ignore_index=True)
        growth_df = calculate_growth_rate(growth_source, growth_start_year, analysis_year)
        result_df = classify_industries(lq_df, growth_df)
    else:
        result_df = lq_df.copy()
        result_df["growth_rate"] = pd.NA
        result_df["industry_type"] = "growth_not_calculated"
    result_df["national_source_tbl_id"] = "DT_1K52F01"
    result_df["local_source"] = "local_business_survey.duckdb"
    return VerifiedLqResult(
        status="ready",
        gate=gate.to_dict(),
        results=result_df.to_dict(orient="records"),
        validation=validation.model_dump(),
    )

