import json
import os
from backend.models import BookmarksData

BOOKMARKS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "bookmarks.json")
BOOKMARKS_PATH = os.path.normpath(BOOKMARKS_PATH)
MAX_BOOKMARKS = 10

def load_bookmarks() -> BookmarksData:
    if not os.path.isfile(BOOKMARKS_PATH):
        return BookmarksData()
    with open(BOOKMARKS_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return BookmarksData(**raw)

def save_bookmarks(data: BookmarksData) -> BookmarksData:
    data.bookmarks = data.bookmarks[:MAX_BOOKMARKS]
    with open(BOOKMARKS_PATH, "w", encoding="utf-8") as f:
        json.dump(data.model_dump(), f, ensure_ascii=False, indent=2)
    return data
