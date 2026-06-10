from pydantic import BaseModel
from typing import Optional, Literal

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

class BookmarksData(BaseModel):
    default: Optional[str] = None
    bookmarks: list[str] = []


class KeyValueItem(BaseModel):
    key: str = ""
    value: str = ""
    enabled: bool = True


class RequestSpec(BaseModel):
    method: str = "GET"
    url: str = ""
    params: list[KeyValueItem] = []
    headers: list[KeyValueItem] = []
    body_type: Literal["none", "json", "raw", "form"] = "none"
    body: str = ""                 # json/raw 文本内容
    form_body: list[KeyValueItem] = []


class ResponseResult(BaseModel):
    status: Optional[int] = None
    status_text: str = ""
    elapsed_ms: float = 0
    size_bytes: int = 0
    headers: dict[str, str] = {}
    content_type: str = ""
    body: str = ""
    truncated: bool = False
    error: Optional[str] = None


class RequestSample(BaseModel):
    id: str
    name: str
    request: RequestSpec


class RequestStore(BaseModel):
    samples: list[RequestSample] = []
    draft: Optional[RequestSpec] = None


class CurlText(BaseModel):
    text: str


class CurlResult(BaseModel):
    curl: str
