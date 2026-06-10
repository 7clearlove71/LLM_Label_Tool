import json
from typing import Iterable, Iterator, Optional, Tuple

import httpx

from backend.models import RequestSpec

DEFAULT_TIMEOUT = 120.0


def transform_sse_lines(lines: Iterable[str]) -> Iterator[Tuple[str, dict]]:
    """把上游 OpenAI 兼容 SSE 行流转换为 (event, data) 事件流。

    - data: [DONE]      -> ("done", {})
    - 含 content/reasoning 的 delta -> ("delta", {"content", "reasoning"})
    - 空行 / 非 data: 行 / 坏 JSON / 无 delta / 空 delta -> 跳过
    reasoning 字段兼容：reasoning_content（DeepSeek/vLLM）-> reasoning（OpenRouter）。
    """
    for raw in lines:
        line = (raw or "").strip()
        if not line.startswith("data:"):
            continue
        payload = line[len("data:"):].strip()
        if payload == "[DONE]":
            yield ("done", {})
            return
        try:
            obj = json.loads(payload)
        except (json.JSONDecodeError, ValueError):
            continue
        try:
            delta = obj["choices"][0]["delta"]
        except (KeyError, IndexError, TypeError):
            continue
        content = delta.get("content") or ""
        reasoning = delta.get("reasoning_content") or delta.get("reasoning") or ""
        if content or reasoning:
            yield ("delta", {"content": content, "reasoning": reasoning})


def format_sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def stream_chat(spec: RequestSpec, client: Optional[httpx.Client] = None) -> Iterator[str]:
    """连接上游 LLM，逐行转发为前端 SSE 字符串。"""
    headers = {h.key: h.value for h in spec.headers if h.enabled and h.key}
    content = spec.body.encode("utf-8") if spec.body else None
    owns = client is None
    try:
        if owns:
            client = httpx.Client(timeout=DEFAULT_TIMEOUT, follow_redirects=True, trust_env=False)
        with client.stream("POST", spec.url, headers=headers or None, content=content) as resp:
            if resp.status_code >= 400:
                body = resp.read().decode("utf-8", "replace")
                yield format_sse("error", {"message": f"上游 {resp.status_code}: {body[:500]}"})
                return
            for event, data in transform_sse_lines(resp.iter_lines()):
                yield format_sse(event, data)
    except Exception as e:  # noqa: BLE001 — 网络/超时统一回退为 error 事件
        yield format_sse("error", {"message": str(e) or e.__class__.__name__})
    finally:
        if owns and client is not None:
            client.close()
