import json
from typing import Optional

def search_file(path: str, keyword: str, field: Optional[str] = None) -> list[dict]:
    results = []
    row_index = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            data = json.loads(stripped)
            matched = False
            if field:
                value = data.get(field)
                if value is not None and keyword in json.dumps(value, ensure_ascii=False):
                    matched = True
            else:
                if keyword in stripped:
                    matched = True
            if matched:
                results.append({"row_index": row_index, "data": data})
            row_index += 1
    return results
