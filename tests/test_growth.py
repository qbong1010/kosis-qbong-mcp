from __future__ import annotations

import pandas as pd

from src.growth import calculate_growth_rate


def test_growth_rate_warns_on_small_base(industry_frame):
    start = industry_frame("강릉시", 2020)
    end = industry_frame("강릉시", 2024)
    start.loc[start["industry_code"] == "C30", "value"] = 5
    end.loc[end["industry_code"] == "C30", "value"] = 15
    df = pd.concat([start, end], ignore_index=True)

    result = calculate_growth_rate(df, 2020, 2024, min_base_value=10)
    c30 = result[result["industry_code"] == "C30"].iloc[0]

    assert c30["growth_rate"] == 200
    assert "과대해석" in c30["growth_warning"]

