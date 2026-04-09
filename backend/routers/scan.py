from fastapi import APIRouter, HTTPException
from backend.models import ScanRequest
from backend.services.scanner import scan_directory

router = APIRouter()

@router.post("/api/scan")
def scan(req: ScanRequest):
    tree = scan_directory(req.path)
    if tree is None:
        raise HTTPException(status_code=400, detail="目录不存在")
    return tree
