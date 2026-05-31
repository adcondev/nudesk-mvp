import re
import json
from datetime import datetime, timezone

def _envelope(data=None, error=None, request_id: str = "") -> dict:
    return {
        "data": data,
        "error": error,
        "meta": {"request_id": request_id, "timestamp": datetime.now(timezone.utc).isoformat()},
    }

def _parse_claude_json(raw: str) -> dict:
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
    return json.loads(raw)
