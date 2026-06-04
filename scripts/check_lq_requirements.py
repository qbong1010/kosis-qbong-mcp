from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data_gate import check_gangneung_lq_requirements


app = typer.Typer(add_completion=False)


@app.command()
def main(
    analysis_year: int = typer.Option(2024),
    indicator: str = typer.Option("both", help="employees, establishments, or both"),
    growth_start_year: int | None = typer.Option(None),
) -> None:
    indicators = ["employees", "establishments"] if indicator == "both" else [indicator]
    result = check_gangneung_lq_requirements(
        analysis_year=analysis_year,
        indicators=indicators,
        growth_start_year=growth_start_year,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    app()

