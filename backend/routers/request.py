from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.models import RequestSpec, ResponseResult, RequestStore, CurlText, CurlResult
from backend.services.http_client import send_request
from backend.services.curl_parser import parse_curl, to_curl
from backend.services.request_store import load_store, save_store
from backend.services.chat_stream import stream_chat

router = APIRouter()


@router.post("/api/request/send")
def send(spec: RequestSpec) -> ResponseResult:
    return send_request(spec)


@router.post("/api/request/chat/stream")
def chat_stream(spec: RequestSpec):
    return StreamingResponse(stream_chat(spec), media_type="text/event-stream")


@router.post("/api/request/parse-curl")
def parse(payload: CurlText) -> RequestSpec:
    try:
        return parse_curl(payload.text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"curl 解析失败：{e}")


@router.post("/api/request/to-curl")
def export(spec: RequestSpec) -> CurlResult:
    return CurlResult(curl=to_curl(spec))


@router.get("/api/requests")
def get_requests() -> RequestStore:
    return load_store()


@router.put("/api/requests")
def put_requests(data: RequestStore) -> RequestStore:
    return save_store(data)
