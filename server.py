from __future__ import annotations

from typing import Any

import pandas as pd
from mcp.server.fastmcp import FastMCP

from src.exporter import validation_report_markdown
from src.kosis_client import KosisClient
from src.local_survey import fetch_local_industry_middle_totals, ingest_gangneung_business_survey, query_local_business_survey
from src.lq import calculate_lq as calculate_lq_frame
from src.metadata import metadata_summary
from src.normalizer import normalize_kosis_data
from src.growth import calculate_growth_rate as calculate_growth_rate_frame
from src.data_gate import check_gangneung_lq_requirements
from src.pipeline import fetch_industry_data as fetch_industry_data_frame
from src.pipeline import find_latest_common_year as find_latest_common_year_frame
from src.pipeline import run_gangneung_lq
from src.validators import validate_lq_inputs as validate_lq_frames
from src.verified_lq import run_verified_gangneung_lq


mcp = FastMCP("KOSIS Industrial Analysis MCP")


def _df(rows: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame.from_records(rows)


@mcp.tool()
def search_kosis_tables(keyword: str) -> list[dict[str, Any]]:
    """Search KOSIS statistic tables by keyword."""
    return KosisClient().search_tables(keyword)


@mcp.tool()
def get_table_metadata(org_id: str, tbl_id: str) -> dict[str, Any]:
    """Fetch and summarize KOSIS table metadata."""
    rows = KosisClient().get_table_metadata(org_id, tbl_id)
    return metadata_summary(rows)


@mcp.tool()
def fetch_industry_data(region: str, years: list[int], indicator: str) -> list[dict[str, Any]]:
    """Fetch normalized manufacturing middle-category industry statistics."""
    return fetch_industry_data_frame(region=region, years=years, indicator=indicator).to_dict(orient="records")


@mcp.tool()
def find_latest_common_year(local_rows: list[dict[str, Any]], national_rows: list[dict[str, Any]]) -> int:
    """Find the latest year available in both local and national rows."""
    return find_latest_common_year_frame(_df(local_rows), _df(national_rows))


@mcp.tool()
def normalize_kosis_data_tool(
    raw_data: list[dict[str, Any]],
    org_id: str,
    tbl_id: str,
    region_code: str,
    region_name: str,
    indicator: str,
    expected_unit: str,
) -> list[dict[str, Any]]:
    """Normalize raw KOSIS rows into the standard industry_stats schema."""
    return normalize_kosis_data(
        raw_data,
        org_id=org_id,
        tbl_id=tbl_id,
        region_code=region_code,
        region_name=region_name,
        indicator=indicator,
        expected_unit=expected_unit,
    ).to_dict(orient="records")


@mcp.tool()
def validate_lq_inputs(local_rows: list[dict[str, Any]], national_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate local and national rows before LQ calculation."""
    return validate_lq_frames(_df(local_rows), _df(national_rows)).model_dump()


@mcp.tool()
def calculate_lq(local_rows: list[dict[str, Any]], national_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Calculate LQ values from validated local and national industry rows."""
    return calculate_lq_frame(_df(local_rows), _df(national_rows)).to_dict(orient="records")


@mcp.tool()
def calculate_growth_rate(rows: list[dict[str, Any]], start_year: int, end_year: int) -> list[dict[str, Any]]:
    """Calculate simple growth rate by industry."""
    return calculate_growth_rate_frame(_df(rows), start_year, end_year).to_dict(orient="records")


@mcp.tool()
def classify_industries(lq_rows: list[dict[str, Any]], growth_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Classify industries by LQ and growth rate."""
    from src.classifier import classify_industries as classify_industries_frame

    return classify_industries_frame(_df(lq_rows), _df(growth_rows)).to_dict(orient="records")


@mcp.tool()
def export_lq_excel(indicator: str = "employees", latest_year: int | None = None) -> dict[str, Any]:
    """Deprecated legacy export entrypoint. Use verified LQ tools after data-gate checks."""
    result = run_verified_gangneung_lq(analysis_year=latest_year or 2024, indicator=indicator)
    return {
        "status": result.status,
        "message": "Legacy export_lq_excel no longer runs unverified analysis. Use run_verified_gangneung_lq_tool.",
        "gate": result.gate,
    }


@mcp.tool()
def generate_validation_report(result: dict[str, Any]) -> str:
    """Generate a Markdown validation report."""
    return validation_report_markdown(result)


@mcp.tool()
def run_gangneung_lq_tool(indicator: str = "employees", latest_year: int | None = None) -> dict[str, Any]:
    """Compatibility wrapper for verified Gangneung LQ. It will not run if required data is missing."""
    result = run_verified_gangneung_lq(analysis_year=latest_year or 2024, indicator=indicator)
    return result.__dict__


@mcp.tool()
def ingest_local_business_survey() -> dict[str, Any]:
    """Archive and normalize Gangneung local government business survey Excel files."""
    return ingest_gangneung_business_survey()


@mcp.tool()
def fetch_local_business_survey_data(
    industry_level: str | None = None,
    indicator: str | None = None,
    admin_area_name: str | None = None,
    breakdown_type: str | None = None,
    breakdown_value: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """Fetch normalized local government business survey observations from DuckDB."""
    return query_local_business_survey(
        industry_level=industry_level,
        indicator=indicator,
        admin_area_name=admin_area_name,
        breakdown_type=breakdown_type,
        breakdown_value=breakdown_value,
        limit=limit,
    )


@mcp.tool()
def fetch_local_industry_middle_totals_tool(manufacturing_only: bool = True) -> list[dict[str, Any]]:
    """Fetch canonical Gangneung local industry middle-category totals for ITA/LQ analysis."""
    return fetch_local_industry_middle_totals(manufacturing_only=manufacturing_only)


@mcp.tool()
def check_lq_data_requirements(
    analysis_year: int = 2024,
    indicators: list[str] | None = None,
    growth_start_year: int | None = None,
) -> dict[str, Any]:
    """Check required local and national data before LQ/ITA analysis; block if anything is missing."""
    return check_gangneung_lq_requirements(
        analysis_year=analysis_year,
        indicators=indicators or ["employees", "establishments"],
        growth_start_year=growth_start_year,
    ).to_dict()


@mcp.tool()
def run_verified_gangneung_lq_tool(
    analysis_year: int = 2024,
    indicator: str = "employees",
    growth_start_year: int | None = None,
) -> dict[str, Any]:
    """Run Gangneung LQ using KOSIS DT_1K52F01 and local survey data only after the data gate passes."""
    result = run_verified_gangneung_lq(
        analysis_year=analysis_year,
        indicator=indicator,
        growth_start_year=growth_start_year,
    )
    return result.__dict__


if __name__ == "__main__":
    mcp.run()
