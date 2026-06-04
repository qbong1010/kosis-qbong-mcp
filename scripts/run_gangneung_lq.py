from __future__ import annotations

import sys
from pathlib import Path

import typer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.verified_lq import run_verified_gangneung_lq


app = typer.Typer(add_completion=False)


@app.command()
def main(
    region: str = typer.Option("gangneung", help="Region key from config/region_codes.yaml"),
    indicator: str = typer.Option("employees", help="employees, establishments, or both"),
    latest_year: int | None = typer.Option(None, help="Override latest common year"),
) -> None:
    if region != "gangneung":
        raise typer.BadParameter("MVP CLI currently supports region=gangneung.")
    indicators = ["employees", "establishments"] if indicator == "both" else [indicator]
    for item in indicators:
        result = run_verified_gangneung_lq(analysis_year=latest_year or 2024, indicator=item)
        typer.echo(f"{item}: status={result.status}, rows={len(result.results)}")
        if result.status != "ready":
            typer.echo(f"missing={result.gate.get('missing_requirements')}")


if __name__ == "__main__":
    app()
