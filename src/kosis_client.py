from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
import json
import re

from .config import get_settings


class KosisClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None, timeout: float = 30.0):
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.kosis_api_key
        self.base_url = (base_url or settings.kosis_base_url).rstrip("/")
        self.timeout = timeout
        if not self.api_key:
            raise ValueError("KOSIS_API_KEY is required. Add it to .env or pass api_key explicitly.")

    def _get(self, endpoint: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        merged = {"method": "getList", "apiKey": self.api_key, "format": "json", **params}
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(url, params=merged)
            response.raise_for_status()
            data = self._parse_response(response.text)
        if isinstance(data, dict) and "err" in data:
            if str(data.get("err")) == "30":
                return []
            raise RuntimeError(f"KOSIS API error: {data}")
        if isinstance(data, dict):
            return data.get("data", [data])
        return data

    @staticmethod
    def _parse_response(text: str) -> Any:
        stripped = text.strip()
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            # KOSIS often returns JavaScript object literals, e.g. [{LIST_NM:"인구"}].
            normalized = re.sub(r"([{,])\s*([A-Za-z_][A-Za-z0-9_]*)\s*:", r'\1"\2":', stripped)
            return json.loads(normalized)

    def search_tables(self, keyword: str) -> list[dict[str, Any]]:
        return self._get(
            "statisticsSearch.do",
            {
                "jsonVD": "Y",
                "searchNm": keyword,
            },
        )

    def get_table_metadata(self, org_id: str, tbl_id: str) -> list[dict[str, Any]]:
        return self.get_table_meta(org_id, tbl_id, "ITM")

    def get_table_meta(self, org_id: str, tbl_id: str, meta_type: str = "ITM") -> list[dict[str, Any]]:
        return self._get(
            "statisticsData.do",
            {
                "method": "getMeta",
                "type": meta_type,
                "orgId": org_id,
                "tblId": tbl_id,
            },
        )

    def fetch_statistics_data(
        self,
        *,
        org_id: str,
        tbl_id: str,
        period: str,
        start_year: int,
        end_year: int,
        item_dimension: str,
        item_id: str,
        region_dimension: str,
        region_code: str,
        industry_dimension: str,
        industry_code: str = "ALL",
        extra_dimensions: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        params = {
            "orgId": org_id,
            "tblId": tbl_id,
            "prdSe": period,
            "startPrdDe": str(start_year),
            "endPrdDe": str(end_year),
            "prdInterval": "1",
            item_dimension: item_id,
            region_dimension: region_code,
            industry_dimension: industry_code,
            "jsonVD": "Y",
        }
        for idx in range(1, 9):
            params.setdefault(f"objL{idx}", "")
        if extra_dimensions:
            params.update(extra_dimensions)
        return self._get("Param/statisticsParameterData.do", params)


def write_raw_json(path: Path, rows: list[dict[str, Any]]) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
