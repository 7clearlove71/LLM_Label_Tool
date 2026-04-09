from fastapi import APIRouter, HTTPException
from backend.models import (
    FileReadRequest, FileReadAllRequest, FileUpdateRequest,
    FileDeleteRequest, FileSaveAsRequest, FileSearchRequest,
)
from backend.services.reader import read_file, read_file_all
from backend.services.schema import detect_schema
from backend.services.editor import update_row, delete_row, save_as
from backend.services.searcher import search_file

router = APIRouter(prefix="/api/file")

@router.post("/read")
def file_read(req: FileReadRequest):
    try:
        result = read_file(req.path, req.offset, req.limit)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="文件不存在")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    schema = detect_schema(result["rows"])
    return {**result, "schema": schema}

@router.post("/read-all")
def file_read_all(req: FileReadAllRequest):
    try:
        result = read_file_all(req.path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="文件不存在")
    schema = detect_schema(result["rows"][:10])
    return {**result, "schema": schema}

@router.post("/update")
def file_update(req: FileUpdateRequest):
    try:
        update_row(req.path, req.row_index, req.data)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="文件不存在")
    except IndexError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok"}

@router.post("/delete")
def file_delete(req: FileDeleteRequest):
    try:
        delete_row(req.path, req.row_index)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="文件不存在")
    except IndexError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok"}

@router.post("/save-as")
def file_save_as(req: FileSaveAsRequest):
    try:
        save_as(req.source_path, req.target_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="源文件不存在")
    return {"status": "ok"}

@router.post("/search")
def file_search(req: FileSearchRequest):
    try:
        results = search_file(req.path, req.keyword, req.field)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="文件不存在")
    return {"results": results, "count": len(results)}
