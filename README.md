# KOSIS Industrial Analysis MCP

KOSIS and local-government business-survey analysis tools for Gangneung industrial LQ/ITA work.

## Setup

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
```

Set `KOSIS_API_KEY` in `.env`.

## Local Business Survey Ingestion

```powershell
python scripts/ingest_gangneung_business_survey.py
```

This archives raw Excel files under:

```text
data/sources/local_gov/gangneung/business_survey/2024/raw/
```

It also creates:

```text
data/processed/local_business_survey.duckdb
data/processed/gangneung_business_survey_2024.parquet
data/processed/gangneung_business_survey_2024_raw_cells.parquet
data/processed/gangneung_business_survey_2024_observations.csv
```

## Data Gate

Always check required data before analysis.

```powershell
python scripts/check_lq_requirements.py --analysis-year 2024 --indicator both
python scripts/check_lq_requirements.py --analysis-year 2024 --indicator both --growth-start-year 2015
```

If required national/local years, indicators, units, or industry codes are missing, the gate returns `blocked` and analysis must not proceed.

## Verified LQ

```powershell
python scripts/run_verified_gangneung_lq.py --analysis-year 2024 --indicator employees
python scripts/run_verified_gangneung_lq.py --analysis-year 2024 --indicator establishments
```

Verified LQ uses:

```text
National: KOSIS DT_1K52F01, orgId=101, objL1=00, objL3=0, itmId=T1/T2
Local:    data/processed/local_business_survey.duckdb
```

## MCP Server

```powershell
python server.py
```

Important MCP tools:

```text
ingest_local_business_survey
fetch_local_business_survey_data
fetch_local_industry_middle_totals_tool
check_lq_data_requirements
run_verified_gangneung_lq_tool
```

