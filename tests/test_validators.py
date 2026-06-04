from __future__ import annotations

from src.validators import validate_lq_inputs


def test_validate_lq_inputs_success_with_total(industry_frame):
    result = validate_lq_inputs(industry_frame("강릉시", 2024), industry_frame("전국", 2024))

    assert result.is_valid is True
    assert result.year == 2024
    assert result.indicator == "employees"


def test_validate_lq_inputs_fails_on_unit_mismatch(industry_frame):
    local = industry_frame("강릉시", 2024, unit="명")
    national = industry_frame("전국", 2024, unit="개")

    result = validate_lq_inputs(local, national)

    assert result.is_valid is False
    assert any("단위" in error for error in result.errors)


def test_validate_lq_inputs_warns_on_suppressed(industry_frame):
    local = industry_frame("강릉시", 2024)
    national = industry_frame("전국", 2024)
    local.loc[local["industry_code"] == "C20", "quality_flag"] = "suppressed"
    local.loc[local["industry_code"] == "C20", "value"] = None

    result = validate_lq_inputs(local, national)

    assert result.is_valid is True
    assert result.excluded_count == 1
    assert any("suppressed" in warning for warning in result.warnings)

