from typing import Any

_CONVERSATION_KEYS = {"role", "content"}
_PREFERENCE_KEYS = {"chosen", "rejected"}
_INSTRUCTION_KEYS = {"instruction", "input", "output"}

def _detect_field_type(values: list[Any]) -> dict:
    non_none = [v for v in values if v is not None]
    if not non_none:
        return {"type": "unknown", "display": "column"}

    sample = non_none[0]

    if isinstance(sample, list):
        if (len(non_none) > 0 and
            all(isinstance(v, list) for v in non_none) and
            any(len(v) > 0 for v in non_none)):
            flat_items = [item for v in non_none for item in v if isinstance(item, dict)]
            if flat_items and _CONVERSATION_KEYS.issubset(flat_items[0].keys()):
                children = [{"name": k, "type": "string"} for k in flat_items[0].keys()]
                return {"type": "array<object>", "display": "detail", "pattern": "conversation", "children": children}
        return {"type": "array", "display": "detail"}

    if isinstance(sample, dict):
        return {"type": "object", "display": "detail"}

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

    field_names: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                field_names.append(key)
                seen.add(key)

    all_keys = set(field_names)
    has_preference = _PREFERENCE_KEYS.issubset(all_keys)
    has_instruction = _INSTRUCTION_KEYS.issubset(all_keys)

    fields = []
    for name in field_names:
        values = [row.get(name) for row in rows]
        field_info = _detect_field_type(values)
        field_info["name"] = name

        if has_preference and name in _PREFERENCE_KEYS:
            field_info["pattern"] = "preference"
            field_info["display"] = "detail"

        if has_instruction and name in _INSTRUCTION_KEYS:
            field_info["pattern"] = "instruction"
            field_info["display"] = "detail"

        fields.append(field_info)

    return {"fields": fields}
