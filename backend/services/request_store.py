import json
import os
from backend.models import RequestStore

REQUESTS_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "requests.json")
)


def load_store() -> RequestStore:
    if not os.path.isfile(REQUESTS_PATH):
        return RequestStore()
    try:
        with open(REQUESTS_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, ValueError):
        # 文件损坏：备份后返回空，避免应用因 500 无法启动
        try:
            os.replace(REQUESTS_PATH, REQUESTS_PATH + ".corrupt")
        except OSError:
            pass
        return RequestStore()
    return RequestStore(**raw)


def save_store(data: RequestStore) -> RequestStore:
    # 原子写：先写临时文件，再 os.replace 替换，避免半截文件
    tmp_path = REQUESTS_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data.model_dump(), f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, REQUESTS_PATH)
    return data
