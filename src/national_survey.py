from __future__ import annotations

from typing import Any

import pandas as pd

from .kosis_client import KosisClient
from .normalizer import parse_value


NATIONAL_BUSINESS_SURVEY = {
    "org_id": "101",
    "tbl_id": "DT_1K52F01",
    "region_code": "00",
    "region_name": "National",
    "establishment_type_total": "0",
    "indicators": {"T1": ("establishments", "EA"), "T2": ("employees", "PERSON")},
}


def fetch_national_business_survey_rows(year: int, client: KosisClient | None = None) -> list[dict[str, Any]]:
    client = client or KosisClient()
    return client.fetch_statistics_data(
        org_id=NATIONAL_BUSINESS_SURVEY["org_id"],
        tbl_id=NATIONAL_BUSINESS_SURVEY["tbl_id"],
        period="Y",
        start_year=year,
        end_year=year,
        item_dimension="itmId",
        item_id="ALL",
        region_dimension="objL1",
        region_code=NATIONAL_BUSINESS_SURVEY["region_code"],
        industry_dimension="objL2",
        industry_code="ALL",
        extra_dimensions={"objL3": NATIONAL_BUSINESS_SURVEY["establishment_type_total"]},
    )


def normalize_national_business_survey(year: int, client: KosisClient | None = None) -> pd.DataFrame:
    rows = fetch_national_business_survey_rows(year, client=client)
    records: list[dict[str, Any]] = []
    for row in rows:
        industry_code = str(row.get("C2") or "").strip()
        if not (industry_code == "C" or pd.Series([industry_code]).str.match(r"^C\d{2}$").iloc[0]):
            continue
        if str(row.get("C3") or "") != NATIONAL_BUSINESS_SURVEY["establishment_type_total"]:
            continue
        item = str(row.get("ITM_ID") or "")
        if item not in NATIONAL_BUSINESS_SURVEY["indicators"]:
            continue
        indicator, unit = NATIONAL_BUSINESS_SURVEY["indicators"][item]
        value, quality_flag = parse_value(row.get("DT"))
        records.append(
            {
                "source": "KOSIS",
                "org_id": NATIONAL_BUSINESS_SURVEY["org_id"],
                "tbl_id": NATIONAL_BUSINESS_SURVEY["tbl_id"],
                "year": int(row.get("PRD_DE") or year),
                "region_code": NATIONAL_BUSINESS_SURVEY["region_code"],
                "region_name": NATIONAL_BUSINESS_SURVEY["region_name"],
                "industry_code": industry_code,
                "industry_name": str(row.get("C2_NM") or industry_code).strip(),
                "industry_level": "major" if industry_code == "C" else "middle",
                "indicator": indicator,
                "unit": unit,
                "value": value,
                "last_modified": row.get("LST_CHN_DE"),
                "quality_flag": quality_flag,
            }
        )
    return pd.DataFrame.from_records(records)

