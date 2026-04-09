import json
import shutil
from backend.services.reader import invalidate_cache

def _read_all_lines(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [line for line in f if line.strip()]

def _write_all_lines(path: str, lines: list[str]):
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            if not line.endswith("\n"):
                line += "\n"
            f.write(line)
    invalidate_cache(path)

def update_row(path: str, row_index: int, data: dict):
    lines = _read_all_lines(path)
    if row_index < 0 or row_index >= len(lines):
        raise IndexError(f"行索引 {row_index} 超出范围（共 {len(lines)} 行）")
    lines[row_index] = json.dumps(data, ensure_ascii=False) + "\n"
    _write_all_lines(path, lines)

def delete_row(path: str, row_index: int):
    lines = _read_all_lines(path)
    if row_index < 0 or row_index >= len(lines):
        raise IndexError(f"行索引 {row_index} 超出范围（共 {len(lines)} 行）")
    lines.pop(row_index)
    _write_all_lines(path, lines)

def save_as(source_path: str, target_path: str):
    shutil.copy2(source_path, target_path)
