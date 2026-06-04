from __future__ import annotations

import pandas as pd

from .validators import total_value


def calculate_lq(local_df: pd.DataFrame, national_df: pd.DataFrame) -> pd.DataFrame:
    local_valid = local_df[local_df["quality_flag"] == "valid"].copy()
    national_valid = national_df[national_df["quality_flag"] == "valid"].copy()
    local_total = total_value(local_valid)
    national_total = total_value(national_valid)

    local_industries = local_valid[local_valid["industry_code"].astype(str).str.match(r"^C\d{2}$", na=False)].copy()
    national_industries = national_valid[national_valid["industry_code"].astype(str).str.match(r"^C\d{2}$", na=False)].copy()

    merged = local_industries.merge(
        national_industries[["industry_code", "industry_name", "value"]],
        on="industry_code",
        how="inner",
        suffixes=("_local", "_national"),
    )
    merged["local_total"] = local_total
    merged["national_total"] = national_total
    merged["local_share"] = merged["value_local"] / local_total
    merged["national_share"] = merged["value_national"] / national_total
    merged["lq"] = merged["local_share"] / merged["national_share"]
    return pd.DataFrame(
        {
            "year": merged["year"],
            "region_name": merged["region_name"],
            "industry_code": merged["industry_code"],
            "industry_name": merged["industry_name_local"],
            "local_value": merged["value_local"],
            "local_total": merged["local_total"],
            "national_value": merged["value_national"],
            "national_total": merged["national_total"],
            "local_share": merged["local_share"],
            "national_share": merged["national_share"],
            "lq": merged["lq"].round(4),
            "indicator": merged["indicator"],
            "unit": merged["unit"],
            "quality_flag": "valid",
            "warnings": "",
        }
    )

