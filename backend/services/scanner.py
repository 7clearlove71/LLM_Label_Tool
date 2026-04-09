import os
from typing import Optional

def scan_directory(path: str) -> Optional[dict]:
    """递归扫描目录，返回仅包含 .json/.jsonl 文件的树形结构"""
    if not os.path.isdir(path):
        return None

    def build_tree(dir_path: str) -> dict:
        node = {
            "name": os.path.basename(dir_path),
            "path": dir_path,
            "type": "directory",
            "children": [],
        }
        try:
            entries = sorted(os.listdir(dir_path))
        except PermissionError:
            return node

        for entry in entries:
            full_path = os.path.join(dir_path, entry)
            if os.path.isdir(full_path):
                child = build_tree(full_path)
                if child["children"]:
                    node["children"].append(child)
            elif entry.endswith((".json", ".jsonl")):
                node["children"].append({
                    "name": entry,
                    "path": full_path,
                    "type": "file",
                    "size": os.path.getsize(full_path),
                })
        return node

    return build_tree(path)
