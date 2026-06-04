from __future__ import annotations

import pandas as pd

from .models import ValidationResult


TOTAL_CODES = {"", "0", "00", "000", "TOTAL", "합계"}


def _single_value(df: pd.DataFrame, column: str) -> object | None:
    if column == "industry_level" and "industry_level" in df.columns:
        df = df[df["industry_level"].isin(["중분류", "middle"])]
    values = df[column].dropna().unique().tolist()
    return values[0] if len(values) == 1 else None


def has_total(df: pd.DataFrame) -> bool:
    codes = set(df["industry_code"].astype(str))
    names = set(df["industry_name"].astype(str))
    return bool(codes & (TOTAL_CODES | {"C"}) or names & {"합계", "계", "전체", "제조업(10~34)"})


def total_value(df: pd.DataFrame) -> float:
    manufacturing_mask = df["industry_code"].astype(str).eq("C")
    if manufacturing_mask.any():
        return float(df.loc[manufacturing_mask, "value"].dropna().sum())
    total_mask = df["industry_code"].astype(str).isin(TOTAL_CODES) | df["industry_name"].astype(str).isin({"합계", "계", "전체"})
    if total_mask.any():
        return float(df.loc[total_mask, "value"].dropna().sum())
    return float(df["value"].dropna().sum())


def validate_lq_inputs(local_df: pd.DataFrame, national_df: pd.DataFrame) -> ValidationResult:
    warnings: list[str] = []
    errors: list[str] = []

    if local_df.empty or national_df.empty:
        errors.append("지역 또는 전국 데이터가 비어 있습니다.")
        return ValidationResult(is_valid=False, errors=errors)

    checks = [
        ("year", "기준연도"),
        ("indicator", "지표"),
        ("unit", "단위"),
        ("industry_level", "산업분류 수준"),
    ]
    for column, label in checks:
        local_value = _single_value(local_df, column)
        national_value = _single_value(national_df, column)
        if local_value is None or national_value is None or local_value != national_value:
            errors.append(f"{label}이 일치하지 않습니다: local={local_value}, national={national_value}")

    excluded_count = int((local_df["quality_flag"] != "valid").sum() + (national_df["quality_flag"] != "valid").sum())
    for _, row in local_df.loc[local_df["quality_flag"] != "valid"].iterrows():
        warnings.append(f"{row['industry_code']} {row['industry_name']}은 {row['quality_flag']} 값으로 제외됩니다.")
    for _, row in national_df.loc[national_df["quality_flag"] != "valid"].iterrows():
        warnings.append(f"전국 {row['industry_code']} {row['industry_name']}은 {row['quality_flag']} 값으로 제외됩니다.")

    local_total = total_value(local_df)
    national_total = total_value(national_df)
    if local_total <= 0 or national_total <= 0:
        errors.append("LQ 계산에 필요한 총계가 0 이하이거나 존재하지 않습니다.")
    elif not has_total(local_df) or not has_total(national_df):
        warnings.append("명시적 총계 행이 없어 유효 산업 행의 합계를 총계로 사용합니다.")

    return ValidationResult(
        is_valid=not errors,
        year=int(_single_value(local_df, "year")) if _single_value(local_df, "year") is not None else None,
        region=str(_single_value(local_df, "region_name")),
        national_region=str(_single_value(national_df, "region_name")),
        indicator=str(_single_value(local_df, "indicator")),
        unit=str(_single_value(local_df, "unit")),
        industry_level=str(_single_value(local_df, "industry_level")),
        row_count=int(len(local_df)),
        excluded_count=excluded_count,
        warnings=warnings,
        errors=errors,
    )
