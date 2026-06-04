from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import duckdb

from .config import ROOT_DIR
from .local_survey import LOCAL_REGION_NAME
from .national_survey import normalize_national_business_survey


MANUFACTURING_CODES = ["C"] + [f"C{i:02d}" for i in range(10, 35)]


@dataclass
class DataGateResult:
    status: str
    analysis_year: int
    indicators: list[str]
    required_years: list[int]
    checks: list[dict[str, Any]] = field(default_factory=list)
    missing_requirements: list[dict[str, Any]] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)

    @property
    def is_ready(self) -> bool:
        return self.status == "ready"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "is_ready": self.is_ready,
            "analysis_year": self.analysis_year,
            "indicators": self.indicators,
            "required_years": self.required_years,
            "checks": self.checks,
            "missing_requirements": self.missing_requirements,
            "alternatives": self.alternatives,
            "requires_user_input": bool(self.missing_requirements),
        }


def _local_db_path() -> str:
    return str(ROOT_DIR / "data" / "processed" / "local_business_survey.duckdb")


def _sql_in_placeholders(values: list[str]) -> str:
    return ",".join(["?"] * len(values))


def _local_available(year: int, indicators: list[str]) -> dict[str, Any]:
    db_path = ROOT_DIR / "data" / "processed" / "local_business_survey.duckdb"
    if not db_path.exists():
        return {"available": False, "reason": "local_business_survey.duckdb is missing", "rows": 0}
    with duckdb.connect(str(db_path), read_only=True) as con:
        df = con.execute(
            f"""
            SELECT survey_year, reference_year, industry_code, indicator, quality_flag, count(*) AS row_count
            FROM business_survey_observations
            WHERE table_no = 3
              AND survey_year = ?
              AND admin_area_name = ?
              AND breakdown_value = '전체'
              AND industry_code IN ({_sql_in_placeholders(MANUFACTURING_CODES)})
              AND indicator IN ({_sql_in_placeholders(indicators)})
            GROUP BY 1,2,3,4,5
            """,
            [year, LOCAL_REGION_NAME, *MANUFACTURING_CODES, *indicators],
        ).fetchdf()
    present = set(zip(df["industry_code"].astype(str), df["indicator"].astype(str))) if not df.empty else set()
    missing_pairs = [
        {"industry_code": code, "indicator": indicator}
        for code in MANUFACTURING_CODES
        for indicator in indicators
        if (code, indicator) not in present
    ]
    return {
        "available": not missing_pairs,
        "source": "local_gov_duckdb",
        "db_path": _local_db_path(),
        "survey_years": sorted(df["survey_year"].dropna().unique().tolist()) if not df.empty else [],
        "reference_years": sorted(df["reference_year"].dropna().unique().tolist()) if not df.empty else [],
        "rows": int(len(df)),
        "missing_pairs": missing_pairs[:20],
        "missing_pair_count": len(missing_pairs),
    }


def _national_available(year: int, indicators: list[str]) -> dict[str, Any]:
    try:
        df = normalize_national_business_survey(year)
    except Exception as exc:
        return {"available": False, "source": "KOSIS", "tbl_id": "DT_1K52F01", "reason": str(exc), "rows": 0}
    if df.empty or "indicator" not in df.columns:
        return {
            "available": False,
            "source": "KOSIS",
            "org_id": "101",
            "tbl_id": "DT_1K52F01",
            "reason": f"no national rows returned for year {year}",
            "years": [],
            "rows": 0,
            "missing_pairs": [{"industry_code": code, "indicator": indicator} for code in MANUFACTURING_CODES for indicator in indicators][:20],
            "missing_pair_count": len(MANUFACTURING_CODES) * len(indicators),
        }
    filtered = df[df["indicator"].isin(indicators)].copy()
    present = set(zip(filtered["industry_code"].astype(str), filtered["indicator"].astype(str))) if not filtered.empty else set()
    missing_pairs = [
        {"industry_code": code, "indicator": indicator}
        for code in MANUFACTURING_CODES
        for indicator in indicators
        if (code, indicator) not in present
    ]
    return {
        "available": not missing_pairs,
        "source": "KOSIS",
        "org_id": "101",
        "tbl_id": "DT_1K52F01",
        "required_params": {"objL1": "00", "objL2": "C,C10-C34", "objL3": "0", "itmId": indicators},
        "years": sorted(filtered["year"].dropna().unique().tolist()) if not filtered.empty else [],
        "rows": int(len(filtered)),
        "missing_pairs": missing_pairs[:20],
        "missing_pair_count": len(missing_pairs),
    }


def check_gangneung_lq_requirements(
    *,
    analysis_year: int,
    indicators: list[str],
    growth_start_year: int | None = None,
) -> DataGateResult:
    required_years = [analysis_year]
    if growth_start_year is not None and growth_start_year not in required_years:
        required_years.insert(0, growth_start_year)

    result = DataGateResult(status="ready", analysis_year=analysis_year, indicators=indicators, required_years=required_years)
    for year in required_years:
        local = _local_available(year, indicators)
        national = _national_available(year, indicators)
        result.checks.append({"scope": "local_gangneung", "year": year, **local})
        result.checks.append({"scope": "national", "year": year, **national})
        if not local["available"]:
            result.missing_requirements.append(
                {
                    "scope": "local_gangneung",
                    "year": year,
                    "source_needed": "Gangneung local government business survey",
                    "reason": local.get("reason") or f"missing {local.get('missing_pair_count')} industry/indicator pairs",
                }
            )
        if not national["available"]:
            result.missing_requirements.append(
                {
                    "scope": "national",
                    "year": year,
                    "source_needed": "KOSIS DT_1K52F01 national business survey",
                    "reason": national.get("reason") or f"missing {national.get('missing_pair_count')} industry/indicator pairs",
                }
            )

    if result.missing_requirements:
        result.status = "blocked"
        result.alternatives = [
            "Add the missing local government business survey files and rerun ingestion.",
            "Use only years available in both national KOSIS and local survey data.",
            "Shorten the growth-rate period to a common available period.",
            "If using another national table, first verify matching population, industry level, indicator, and unit.",
        ]
    return result


def local_lq_frame(analysis_year: int, indicator: str):
    with duckdb.connect(_local_db_path(), read_only=True) as con:
        return con.execute(
            f"""
            SELECT
              survey_year AS year,
              region_code,
              'Gangneung-si' AS region_name,
              industry_code,
              industry_name,
              CASE WHEN industry_code = 'C' THEN 'major' ELSE 'middle' END AS industry_level,
              indicator,
              CASE WHEN indicator = 'establishments' THEN 'EA' ELSE 'PERSON' END AS unit,
              value,
              quality_flag,
              source_file
            FROM business_survey_observations
            WHERE table_no = 3
              AND survey_year = ?
              AND admin_area_name = ?
              AND breakdown_value = '전체'
              AND industry_code IN ({_sql_in_placeholders(MANUFACTURING_CODES)})
              AND indicator = ?
            """,
            [analysis_year, LOCAL_REGION_NAME, *MANUFACTURING_CODES, indicator],
        ).fetchdf()
