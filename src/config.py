from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    kosis_api_key: str = ""
    kosis_base_url: str = "https://kosis.kr/openapi"

    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def load_yaml(path: str | Path) -> dict[str, Any]:
    resolved = ROOT_DIR / path if not Path(path).is_absolute() else Path(path)
    with resolved.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_table_config(name: str = "industrial_business_survey") -> dict[str, Any]:
    tables = load_yaml("config/kosis_tables.yaml")
    return tables[name]


def load_regions() -> dict[str, Any]:
    return load_yaml("config/region_codes.yaml")


def load_rules() -> dict[str, Any]:
    return load_yaml("config/analysis_rules.yaml")

