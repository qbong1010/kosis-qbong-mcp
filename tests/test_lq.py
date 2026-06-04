from __future__ import annotations

from src.lq import calculate_lq


def test_calculate_lq(industry_frame):
    local = industry_frame("강릉시", 2024)
    national = industry_frame("전국", 2024)

    result = calculate_lq(local, national)
    c10 = result[result["industry_code"] == "C10"].iloc[0]

    assert c10["local_share"] == 0.2
    assert c10["national_share"] == 0.1
    assert c10["lq"] == 2.0

