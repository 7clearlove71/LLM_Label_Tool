import json
from typing import Optional

_line_count_cache: dict[str, int] = {}

def get_line_count(path: str) -> int:
    if path in _line_count_cache:
        return _line_count_cache[path]
    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    _line_count_cache[path] = count
    return count

def _read_lines(path: str, offset: int, limit: int) -> list[dict]:
    rows = []
    current = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            if current >= offset:
                rows.append(json.loads(stripped))
                if len(rows) >= limit:
                    break
            current += 1
    return rows

def read_file(path: str, offset: int = 0, limit: int = 10) -> dict:
    total = get_line_count(path)
    rows = _read_lines(path, offset, limit)
    return {"rows": rows, "total": total}

def read_file_all(path: str) -> dict:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return {"rows": rows, "total": len(rows)}

def invalidate_cache(path: str):
    _line_count_cache.pop(path, None)
