from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.local_survey import ingest_gangneung_business_survey


if __name__ == "__main__":
    result = ingest_gangneung_business_survey()
    print(json.dumps(result, ensure_ascii=False, indent=2))

