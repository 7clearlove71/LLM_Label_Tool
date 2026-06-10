import json
from typing import Iterable, Iterator, Tuple


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
