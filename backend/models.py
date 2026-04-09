from pydantic import BaseModel
from typing import Optional

class ScanRequest(BaseModel):
    path: str

class FileReadRequest(BaseModel):
    path: str
    offset: int = 0
    limit: int = 10

class FileReadAllRequest(BaseModel):
    path: str

class FileUpdateRequest(BaseModel):
    path: str
    row_index: int
    data: dict

class FileDeleteRequest(BaseModel):
    path: str
    row_index: int

class FileSaveAsRequest(BaseModel):
    source_path: str
    target_path: str

class FileSearchRequest(BaseModel):
    path: str
    keyword: str
    field: Optional[str] = None
