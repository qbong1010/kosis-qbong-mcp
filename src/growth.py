from __future__ import annotations

import pandas as pd


def calculate_growth_rate(df: pd.DataFrame, start_year: int, end_year: int, min_base_value: float = 10) -> pd.DataFrame:
    valid = df[df["quality_flag"] == "valid"].copy()
    start = valid[valid["year"] == start_year][["industry_code", "value"]].rename(columns={"value": "start_value"})
    end = valid[valid["year"] == end_year][["industry_code", "industry_name", "value"]].rename(columns={"value": "end_value"})
    merged = end.merge(start, on="industry_code", how="left")
    merged["growth_rate"] = ((merged["end_value"] - merged["start_value"]) / merged["start_value"] * 100).round(2)
    merged.loc[merged["start_value"].isna() | (merged["start_value"] <= 0), "growth_rate"] = pd.NA
    merged["growth_warning"] = ""
    merged.loc[merged["start_value"] < min_base_value, "growth_warning"] = "기준연도 값이 작아 성장률 과대해석 주의"
    return merged[["industry_code", "industry_name", "start_value", "end_value", "growth_rate", "growth_warning"]]

