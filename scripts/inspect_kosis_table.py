from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.kosis_client import KosisClient


app = typer.Typer(add_completion=False)


@app.command()
def main(keyword: str = typer.Option(..., help="KOSIS table search keyword")) -> None:
    client = KosisClient()
    rows = client.search_tables(keyword)
    typer.echo(json.dumps(rows[:30], ensure_ascii=False, indent=2))
    typer.echo(f"\nmatched_count={len(rows)}")


if __name__ == "__main__":
    app()
