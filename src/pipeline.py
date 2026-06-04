from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .classifier import classify_industries
from .config import ROOT_DIR, load_regions, load_rules, load_table_config
from .exporter import export_lq_excel, write_validation_report
from .growth import calculate_growth_rate
from .kosis_client import KosisClient, write_raw_json
from .lq import calculate_lq
from .normalizer import filter_manufacturing_middle, normalize_kosis_data
from .validators import validate_lq_inputs


@dataclass(frozen=True)
class AnalysisArtifacts:
    local_df: pd.DataFrame
    national_df: pd.DataFrame
    lq_df: pd.DataFrame
    growth_df: pd.DataFrame
    result_df: pd.DataFrame
    validation: dict[str, Any]
    excel_path: str | None = None
    report_path: str | None = None


def _year_window(latest_year: int, period: int) -> tuple[int, int]:
    return latest_year - period + 1, latest_year


def fetch_industry_data(
    *,
    region: str,
    years: list[int],
    indicator: str,
    client: KosisClient | None = None,
    table_name: str = "industrial_business_survey",
) -> pd.DataFrame:
    table = load_table_config(table_name)
    regions = load_regions()
    region_cfg = regions[region]
    indicator_cfg = table["indicators"][indicator]
    dims = table["dimensions"]
    client = client or KosisClient()

    raw = client.fetch_statistics_data(
        org_id=table["org_id"],
        tbl_id=table["tbl_id"],
        period=table.get("period", "Y"),
        start_year=min(years),
        end_year=max(years),
        item_dimension=dims["item"],
        item_id=indicator_cfg["item_id"],
        region_dimension=dims["region"],
        region_code=region_cfg["code"],
        industry_dimension=dims["industry"],
    )
    write_raw_json(
        ROOT_DIR / "data" / "raw" / f"kosis_{region}_{indicator}_{min(years)}_{max(years)}.json",
        raw,
    )
    normalized = normalize_kosis_data(
        raw,
        org_id=table["org_id"],
        tbl_id=table["tbl_id"],
        region_code=region_cfg["code"],
        region_name=region_cfg["name"],
        indicator=indicator,
        expected_unit=indicator_cfg["unit"],
    )
    filtered = filter_manufacturing_middle(normalized)
    processed_path = ROOT_DIR / "data" / "processed" / f"{region}_industry_stats_{indicator}_{min(years)}_{max(years)}.csv"
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    filtered.to_csv(processed_path, index=False, encoding="utf-8-sig")
    return filtered


def find_latest_common_year(local_df: pd.DataFrame, national_df: pd.DataFrame) -> int:
    local_years = set(local_df["year"].astype(int))
    national_years = set(national_df["year"].astype(int))
    common = sorted(local_years & national_years)
    if not common:
        raise ValueError("전국과 지역의 공통 연도가 없습니다.")
    return common[-1]


def analyze_lq_from_frames(
    *,
    local_df: pd.DataFrame,
    national_df: pd.DataFrame,
    latest_year: int | None = None,
    indicator: str,
) -> AnalysisArtifacts:
    rules = load_rules()
    latest = latest_year or find_latest_common_year(local_df, national_df)
    start_year, end_year = _year_window(latest, int(rules["growth"]["default_period"]))

    local_latest = local_df[local_df["year"] == latest].copy()
    national_latest = national_df[national_df["year"] == latest].copy()
    validation = validate_lq_inputs(local_latest, national_latest)
    if not validation.is_valid:
        return AnalysisArtifacts(
            local_df=local_df,
            national_df=national_df,
            lq_df=pd.DataFrame(),
            growth_df=pd.DataFrame(),
            result_df=pd.DataFrame(),
            validation=validation.model_dump(),
        )

    lq_df = calculate_lq(local_latest, national_latest)
    growth_df = calculate_growth_rate(
        local_df,
        start_year,
        end_year,
        min_base_value=float(rules["growth"]["min_base_value"]),
    )
    result_df = classify_industries(lq_df, growth_df)
    small = rules["quality_rules"]["small_sample_warning"]
    threshold = small["employees_min"] if indicator == "employees" else small["establishments_min"]
    result_df.loc[result_df["local_value"] < threshold, "warnings"] = (
        result_df.loc[result_df["local_value"] < threshold, "warnings"].fillna("").astype(str)
        + f"; 소규모 표본 기준 미달({threshold} 미만)"
    ).str.strip("; ")

    return AnalysisArtifacts(
        local_df=local_df,
        national_df=national_df,
        lq_df=lq_df,
        growth_df=growth_df,
        result_df=result_df,
        validation=validation.model_dump(),
    )


def run_gangneung_lq(
    *,
    indicator: str,
    latest_year: int | None = None,
    client: KosisClient | None = None,
    export: bool = True,
) -> AnalysisArtifacts:
    rules = load_rules()
    if latest_year is None:
        # Broad window used to discover available common years, then the latest 5-year window is analyzed.
        probe_years = list(range(2015, 2031))
    else:
        start, end = _year_window(latest_year, int(rules["growth"]["default_period"]))
        probe_years = list(range(start, end + 1))

    local_df = fetch_industry_data(region="gangneung", years=probe_years, indicator=indicator, client=client)
    national_df = fetch_industry_data(region="national", years=probe_years, indicator=indicator, client=client)
    artifacts = analyze_lq_from_frames(
        local_df=local_df,
        national_df=national_df,
        latest_year=latest_year,
        indicator=indicator,
    )
    if not export:
        return artifacts

    latest = artifacts.validation.get("year") or latest_year or "unknown"
    readme = pd.DataFrame(
        [
            {"항목": "분석지역", "내용": "강릉시"},
            {"항목": "비교지역", "내용": "전국"},
            {"항목": "기준연도", "내용": latest},
            {"항목": "지표", "내용": indicator},
            {"항목": "산업분류", "내용": "제조업 중분류"},
        ]
    )
    validation_df = pd.DataFrame(
        [{"type": "warning", "message": msg} for msg in artifacts.validation.get("warnings", [])]
        + [{"type": "error", "message": msg} for msg in artifacts.validation.get("errors", [])]
    )
    excel_path = export_lq_excel(
        path=Path("outputs") / "excel" / f"gangneung_lq_{indicator}.xlsx",
        readme=readme,
        raw_local=artifacts.local_df,
        raw_national=artifacts.national_df,
        lq_employees=artifacts.result_df if indicator == "employees" else None,
        lq_establishments=artifacts.result_df if indicator == "establishments" else None,
        growth=artifacts.growth_df,
        positioning=artifacts.result_df[["industry_code", "industry_name", "lq", "growth_rate", "industry_type", "warnings"]]
        if not artifacts.result_df.empty
        else None,
        validation=validation_df,
        summary=artifacts.result_df,
    )
    report_path = write_validation_report(
        Path("outputs") / "reports" / f"gangneung_lq_{indicator}_validation_report.md",
        artifacts.validation,
    )
    write_validation_report(
        Path("outputs") / "reports" / "gangneung_lq_validation_report.md",
        artifacts.validation,
    )
    return AnalysisArtifacts(
        local_df=artifacts.local_df,
        national_df=artifacts.national_df,
        lq_df=artifacts.lq_df,
        growth_df=artifacts.growth_df,
        result_df=artifacts.result_df,
        validation=artifacts.validation,
        excel_path=str(excel_path),
        report_path=str(report_path),
    )
