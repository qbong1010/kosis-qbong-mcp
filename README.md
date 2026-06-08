# KOSIS 강릉 산업분석 MCP

KOSIS 국가 통계와 강릉시 사업체조사 원자료를 함께 사용해 제조업 중분류 기준 LQ(Location Quotient)와 성장률 기반 산업 유형 분석을 수행하는 MCP 서버입니다.

이 저장소의 핵심 목적은 LLM 대화 세션에서 필요한 순간에 KOSIS 검색, 통계 메타데이터 조회, 지역/전국 산업 데이터 정규화, 데이터 가용성 검증, 검증된 강릉 LQ 분석을 도구 호출로 실행할 수 있게 하는 것입니다.

## 작동 방식

`server.py`가 FastMCP 서버의 진입점입니다. Codex 같은 MCP 클라이언트가 이 파일을 `stdio` 방식으로 실행하면, 서버는 표준입출력을 통해 JSON-RPC 메시지를 주고받으며 등록된 Python 함수를 MCP 도구로 노출합니다.

전체 흐름은 다음과 같습니다.

1. Codex가 `.codex/config.toml`의 `mcp_servers.kosis_qbong` 설정을 읽고 `server.py`를 실행합니다.
2. `server.py`는 `search_kosis_tables`, `get_table_metadata`, `fetch_industry_data`, `check_lq_data_requirements`, `run_verified_gangneung_lq_tool` 같은 도구를 등록합니다.
3. LLM 대화 중 사용자가 통계 검색이나 분석을 요청하면 Codex가 필요한 MCP 도구를 호출합니다.
4. KOSIS 관련 도구는 `.env`의 `KOSIS_API_KEY`를 사용해 KOSIS API를 호출하고, 응답을 표준 산업 통계 스키마로 정규화합니다.
5. 로컬 강릉 사업체조사 도구는 Excel 원자료를 보관한 뒤 DuckDB/Parquet/CSV 분석용 데이터로 변환합니다.
6. LQ 분석은 먼저 데이터 게이트를 통과해야 합니다. 필요한 연도, 지표, 단위, 산업코드가 지역/전국 양쪽에 모두 있을 때만 계산을 진행합니다.
7. 검증을 통과하면 강릉 지역 값과 전국 값을 비교해 제조업 중분류별 LQ를 계산하고, 선택적으로 성장률을 붙여 산업 유형을 분류합니다.

`stdio`는 통신 방식입니다. 서버를 언제 시작하고 종료할지는 MCP 클라이언트 정책에 따릅니다. 일반적으로 Codex 세션에서 MCP 서버가 로드되면 도구 호출이 가능한 동안 프로세스가 유지되고, 세션 종료나 재시작, 설정 변경 시 종료/재시작됩니다.

## 설치

PowerShell에서 실행합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
```

`.env`에 KOSIS API 키를 설정합니다.

```text
KOSIS_API_KEY=발급받은_API_키
```

## Codex MCP 등록

이 워크스페이스는 로컬 Codex 설정에 다음 형태로 등록합니다.

```toml
[mcp_servers.kosis_qbong]
command = 'C:\Users\Joey\kosis-qbong-mcp\.venv\Scripts\python.exe'
args = ['C:\Users\Joey\kosis-qbong-mcp\server.py']
```

MCP 서버 설정을 바꾼 뒤에는 Codex를 재시작해야 `kosis_qbong` 도구가 새로 로드됩니다.

## 주요 MCP 도구

```text
search_kosis_tables
get_table_metadata
fetch_industry_data
normalize_kosis_data_tool
ingest_local_business_survey
fetch_local_business_survey_data
fetch_local_industry_middle_totals_tool
check_lq_data_requirements
run_verified_gangneung_lq_tool
```

자주 쓰는 도구의 역할은 다음과 같습니다.

- `search_kosis_tables`: 키워드로 KOSIS 통계표를 검색합니다.
- `get_table_metadata`: KOSIS 통계표의 항목 메타데이터를 요약합니다.
- `fetch_industry_data`: KOSIS 산업 통계를 가져와 제조업 중분류 기준으로 정규화합니다.
- `ingest_local_business_survey`: 강릉시 사업체조사 Excel 원자료를 보관하고 분석용 DuckDB/Parquet/CSV로 변환합니다.
- `check_lq_data_requirements`: LQ/ITA 분석 전에 필수 지역/전국 데이터가 모두 있는지 확인합니다.
- `run_verified_gangneung_lq_tool`: 데이터 게이트가 통과된 경우에만 강릉 제조업 LQ 분석을 실행합니다.

## 로컬 사업체조사 적재

```powershell
python scripts/ingest_gangneung_business_survey.py
```

원본 Excel 파일은 다음 위치에 보관됩니다.

```text
data/sources/local_gov/gangneung/business_survey/2024/raw/
```

적재가 끝나면 다음 분석용 파일이 생성됩니다.

```text
data/processed/local_business_survey.duckdb
data/processed/gangneung_business_survey_2024.parquet
data/processed/gangneung_business_survey_2024_raw_cells.parquet
data/processed/gangneung_business_survey_2024_observations.csv
```

## 데이터 게이트

분석 전에 필요한 데이터가 모두 있는지 반드시 확인합니다.

```powershell
python scripts/check_lq_requirements.py --analysis-year 2024 --indicator both
python scripts/check_lq_requirements.py --analysis-year 2024 --indicator both --growth-start-year 2015
```

전국/지역 연도, 지표, 단위, 산업코드 중 하나라도 부족하면 상태가 `blocked`로 반환되며 분석을 진행하지 않습니다.

## 검증된 LQ 분석

```powershell
python scripts/run_verified_gangneung_lq.py --analysis-year 2024 --indicator employees
python scripts/run_verified_gangneung_lq.py --analysis-year 2024 --indicator establishments
```

검증된 LQ 분석은 다음 원천만 사용합니다.

```text
전국: KOSIS DT_1K52F01, orgId=101, objL1=00, objL3=0, itmId=T1/T2
지역: data/processed/local_business_survey.duckdb
```

## 개발 확인

```powershell
python -m pytest
python server.py
```

`python server.py`는 MCP 클라이언트가 `stdio`로 실행할 때 사용하는 서버 진입점입니다. 일반 터미널에서 실행하면 서버가 표준입출력으로 대기하므로, 단독 실행보다는 Codex MCP 설정을 통해 호출하는 방식이 일반적입니다.
