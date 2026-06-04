from __future__ import annotations

import pandas as pd

from src.classifier import classify_industries


def test_classify_industries_boundaries():
    lq = pd.DataFrame(
        [
            {"industry_code": "C10", "industry_name": "A", "lq": 1.0, "warnings": ""},
            {"industry_code": "C20", "industry_name": "B", "lq": 0.9, "warnings": ""},
            {"industry_code": "C30", "industry_name": "C", "lq": 1.1, "warnings": ""},
            {"industry_code": "C40", "industry_name": "D", "lq": 0.8, "warnings": ""},
        ]
    )
    growth = pd.DataFrame(
        [
            {"industry_code": "C10", "growth_rate": 0, "growth_warning": ""},
            {"industry_code": "C20", "growth_rate": 1, "growth_warning": ""},
            {"industry_code": "C30", "growth_rate": -1, "growth_warning": ""},
            {"industry_code": "C40", "growth_rate": -1, "growth_warning": ""},
        ]
    )

    result = classify_industries(lq, growth).set_index("industry_code")

    assert result.loc["C10", "industry_type"] == "선도산업"
    assert result.loc["C20", "industry_type"] == "신흥산업"
    assert result.loc["C30", "industry_type"] == "성숙/기반산업"
    assert result.loc["C40", "industry_type"] == "취약/쇠퇴산업"

