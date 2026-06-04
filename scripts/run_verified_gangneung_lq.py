from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.verified_lq import run_verified_gangneung_lq


app = typer.Typer(add_completion=False)


@app.command()
def main(
    analysis_year: int = typer.Option(2024),
    indicator: str = typer.Option("employees", help="employees or establishments"),
    growth_start_year: int | None = typer.Option(None),
) -> None:
    result = run_verified_gangneung_lq(
        analysis_year=analysis_year,
        indicator=indicator,
        growth_start_year=growth_start_year,
    )
    print(json.dumps(result.__dict__, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    app()

