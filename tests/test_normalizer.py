from __future__ import annotations

from src.normalizer import normalize_kosis_data


def test_suppressed_value_is_not_zero():
    rows = [{"PRD_DE": "2024", "C2": "C19", "C2_NM": "코크스 제조업", "UNIT_NM": "명", "DT": "X"}]

    df = normalize_kosis_data(
        rows,
        org_id="101",
        tbl_id="DT_TEST",
        region_code="42150",
        region_name="강릉시",
        indicator="employees",
        expected_unit="명",
    )

    assert df.iloc[0]["value"] is None
    assert df.iloc[0]["quality_flag"] == "suppressed"

