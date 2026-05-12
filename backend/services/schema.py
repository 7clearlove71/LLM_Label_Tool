from typing import Any


def _detect_fields_recursive(rows_or_dicts: list[dict]) -> list[dict]:
    """从一组字典中递归检测所有字段的 schema。"""
    if not rows_or_dicts:
        return []

    field_names: list[str] = []
    seen: set[str] = set()
    for row in rows_or_dicts:
        if not isinstance(row, dict):
            continue
        for key in row.keys():
            if key not in seen:
                field_names.append(key)
                seen.add(key)

    fields = []
    for name in field_names:
        values = [row.get(name) for row in rows_or_dicts if isinstance(row, dict)]
        field_info = _detect_field_type(values)
        field_info["name"] = name
        fields.append(field_info)

    return fields


def _detect_field_type(values: list[Any]) -> dict:
    non_none = [v for v in values if v is not None]
    if not non_none:
        return {"type": "unknown", "display": "column"}

    sample = non_none[0]

    if isinstance(sample, list):
        if all(isinstance(v, list) for v in non_none):
            flat_items = [item for v in non_none for item in v if isinstance(item, dict)]
            if flat_items:
                children = _detect_fields_recursive(flat_items)
                return {"type": "array<object>", "display": "detail", "children": children}
        return {"type": "array", "display": "detail"}

    if isinstance(sample, dict):
        all_dicts = [v for v in non_none if isinstance(v, dict)]
        children = _detect_fields_recursive(all_dicts)
        return {"type": "object", "display": "detail", "children": children}

    if isinstance(sample, bool):
        return {"type": "boolean", "display": "column"}

    if isinstance(sample, (int, float)):
        return {"type": "number", "display": "column"}

    if isinstance(sample, str):
        max_len = max(len(str(v)) for v in non_none)
        if max_len >= 100:
            return {"type": "string", "display": "detail"}
        return {"type": "string", "display": "column"}

    return {"type": "unknown", "display": "column"}


def detect_schema(rows: list[dict]) -> dict:
    if not rows:
        return {"fields": []}

    return {"fields": _detect_fields_recursive(rows)}
