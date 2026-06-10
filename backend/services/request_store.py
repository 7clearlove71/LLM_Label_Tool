import json
import os
from backend.models import RequestStore

REQUESTS_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "requests.json")
)


def load_store() -> RequestStore:
    if not os.path.isfile(REQUESTS_PATH):
        return RequestStore()
    with open(REQUESTS_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return RequestStore(**raw)


def save_store(data: RequestStore) -> RequestStore:
    with open(REQUESTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data.model_dump(), f, ensure_ascii=False, indent=2)
    return data
