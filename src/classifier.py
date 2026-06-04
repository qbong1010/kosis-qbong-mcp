from __future__ import annotations

import pandas as pd


def classify_industries(lq_df: pd.DataFrame, growth_df: pd.DataFrame) -> pd.DataFrame:
    result = lq_df.merge(
        growth_df[["industry_code", "growth_rate", "growth_warning"]],
        on="industry_code",
        how="left",
    )

    def classify(row: pd.Series) -> str:
        lq = row["lq"]
        growth = row["growth_rate"]
        if pd.isna(growth):
            return "분류불가"
        if lq >= 1.0 and growth >= 0:
            return "선도산업"
        if lq < 1.0 and growth >= 0:
            return "신흥산업"
        if lq >= 1.0 and growth < 0:
            return "성숙/기반산업"
        return "취약/쇠퇴산업"

    result["industry_type"] = result.apply(classify, axis=1)
    result["warnings"] = result[["warnings", "growth_warning"]].fillna("").agg("; ".join, axis=1).str.strip("; ")
    return result.drop(columns=["growth_warning"])

