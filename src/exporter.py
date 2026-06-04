from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .config import ROOT_DIR
from .models import ValidationResult


def export_lq_excel(
    *,
    path: str | Path,
    readme: pd.DataFrame,
    raw_local: pd.DataFrame,
    raw_national: pd.DataFrame,
    lq_employees: pd.DataFrame | None = None,
    lq_establishments: pd.DataFrame | None = None,
    growth: pd.DataFrame | None = None,
    positioning: pd.DataFrame | None = None,
    validation: pd.DataFrame | None = None,
    summary: pd.DataFrame | None = None,
) -> Path:
    resolved = ROOT_DIR / path if not Path(path).is_absolute() else Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(resolved, engine="openpyxl") as writer:
        readme.to_excel(writer, sheet_name="README", index=False)
        raw_local.to_excel(writer, sheet_name="raw_local", index=False)
        raw_national.to_excel(writer, sheet_name="raw_national", index=False)
        if lq_employees is not None:
            lq_employees.to_excel(writer, sheet_name="lq_employees", index=False)
        if lq_establishments is not None:
            lq_establishments.to_excel(writer, sheet_name="lq_establishments", index=False)
        if growth is not None:
            growth.to_excel(writer, sheet_name="growth", index=False)
        if positioning is not None:
            positioning.to_excel(writer, sheet_name="positioning", index=False)
        if validation is not None:
            validation.to_excel(writer, sheet_name="validation", index=False)
        if summary is not None:
            summary.to_excel(writer, sheet_name="summary", index=False)
    return resolved


def validation_report_markdown(result: ValidationResult | dict[str, Any]) -> str:
    data = result.model_dump() if isinstance(result, ValidationResult) else result
    lines = [
        "# KOSIS LQ Validation Report",
        "",
        f"- valid: {data.get('is_valid')}",
        f"- year: {data.get('year')}",
        f"- region: {data.get('region')}",
        f"- national_region: {data.get('national_region')}",
        f"- indicator: {data.get('indicator')}",
        f"- unit: {data.get('unit')}",
        f"- industry_level: {data.get('industry_level')}",
        f"- row_count: {data.get('row_count')}",
        f"- excluded_count: {data.get('excluded_count')}",
        "",
        "## Warnings",
    ]
    warnings = data.get("warnings") or []
    lines.extend([f"- {warning}" for warning in warnings] or ["- 없음"])
    lines.extend(["", "## Errors"])
    errors = data.get("errors") or []
    lines.extend([f"- {error}" for error in errors] or ["- 없음"])
    return "\n".join(lines) + "\n"


def write_validation_report(path: str | Path, result: ValidationResult | dict[str, Any]) -> Path:
    resolved = ROOT_DIR / path if not Path(path).is_absolute() else Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(validation_report_markdown(result), encoding="utf-8")
    return resolved

