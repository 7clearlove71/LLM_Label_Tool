from fastapi import APIRouter
from backend.models import BookmarksData
from backend.services.bookmark import load_bookmarks, save_bookmarks

router = APIRouter()

@router.get("/api/bookmarks")
def get_bookmarks() -> BookmarksData:
    return load_bookmarks()

@router.put("/api/bookmarks")
def put_bookmarks(data: BookmarksData) -> BookmarksData:
    return save_bookmarks(data)
