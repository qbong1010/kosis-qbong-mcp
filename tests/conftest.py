from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def industry_frame():
    def make(region_name: str, year: int, indicator: str = "employees", unit: str = "명") -> pd.DataFrame:
        region_code = "42150" if region_name == "강릉시" else "00"
        values = {
            "합계": 1000 if region_name == "강릉시" else 100000,
            "C10": 200 if region_name == "강릉시" else 10000,
            "C20": 50 if region_name == "강릉시" else 10000,
            "C30": 5 if region_name == "강릉시" else 5000,
        }
        names = {
            "합계": "합계",
            "C10": "식료품 제조업",
            "C20": "화학물질 및 화학제품 제조업",
            "C30": "자동차 및 트레일러 제조업",
        }
        return pd.DataFrame(
            [
                {
                    "source": "KOSIS",
                    "org_id": "101",
                    "tbl_id": "DT_TEST",
                    "year": year,
                    "region_code": region_code,
                    "region_name": region_name,
                    "industry_code": code,
                    "industry_name": names[code],
                    "industry_level": "중분류",
                    "indicator": indicator,
                    "unit": unit,
                    "value": value,
                    "quality_flag": "valid",
                }
                for code, value in values.items()
            ]
        )

    return make
