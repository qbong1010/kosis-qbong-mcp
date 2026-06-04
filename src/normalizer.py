from __future__ import annotations

import re
from typing import Any

import pandas as pd

from .models import IndustryStat


SUPPRESSED_VALUES = {"-", "X", "x", "...", "…", ""}


def _first(row: dict[str, Any], keys: tuple[str, ...], default: Any = None) -> Any:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return default


def parse_value(value: Any) -> tuple[float | None, str]:
    if value is None:
        return None, "missing"
    text = str(value).strip().replace(",", "")
    if text in SUPPRESSED_VALUES:
        return None, "suppressed"
    try:
        return float(text), "valid"
    except ValueError:
        return None, "missing"


def infer_industry_level(industry_code: str, industry_name: str) -> str:
    code = industry_code.strip()
    if re.fullmatch(r"[A-Z]\d{2}", code):
        return "중분류"
    if re.fullmatch(r"[A-Z]", code):
        return "대분류"
    if re.fullmatch(r"[A-Z]\d{3}", code):
        return "소분류"
    if re.fullmatch(r"[A-Z]\d{4}", code):
        return "세분류"
    if re.fullmatch(r"[A-Z]\d{5}", code):
        return "세세분류"
    if code in {"0", "00", "000"} or industry_name in {"합계", "계", "전체", "전체 산업", "광업 및 제조업"}:
        return "총계"
    if "제조업" in industry_name and len(code) <= 3:
        return "중분류"
    return "unknown"


def normalize_kosis_data(
    raw_data: list[dict[str, Any]],
    *,
    org_id: str,
    tbl_id: str,
    region_code: str,
    region_name: str,
    indicator: str,
    expected_unit: str,
    default_industry_level: str = "중분류",
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for row in raw_data:
        year = int(_first(row, ("PRD_DE", "PRD_DE_NM", "year", "YEAR")))
        industry_code = str(_first(row, ("C2", "C2_ID", "OBJL2", "OBJL2_ID", "industry_code"), "")).strip()
        industry_name = str(_first(row, ("C2_NM", "OBJL2_NM", "ITM_NM", "industry_name"), industry_code)).strip()
        unit = str(_first(row, ("UNIT_NM", "UNIT", "unit"), expected_unit)).strip()
        value, quality_flag = parse_value(_first(row, ("DT", "value", "VALUE")))
        level = infer_industry_level(industry_code, industry_name)
        if level == "unknown":
            level = default_industry_level
        records.append(
            IndustryStat(
                org_id=org_id,
                tbl_id=tbl_id,
                year=year,
                region_code=region_code,
                region_name=region_name,
                industry_code=industry_code,
                industry_name=industry_name,
                industry_level=level,
                indicator=indicator,
                unit=unit,
                value=value,
                quality_flag=quality_flag,
                raw=row,
            ).model_dump(exclude={"raw"})
        )
    return pd.DataFrame.from_records(records)


def filter_manufacturing_middle(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    codes = df["industry_code"].astype(str)
    mask = codes.str.match(r"^C\d{2}$") | codes.isin(["0", "C"])
    return df.loc[mask].copy()
