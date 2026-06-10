from backend.services.chat_stream import transform_sse_lines, format_sse


def collect(lines):
    return list(transform_sse_lines(lines))


def test_content_delta():
    events = collect(['data: {"choices":[{"delta":{"content":"你好"}}]}'])
    assert events == [("delta", {"content": "你好", "reasoning": ""})]


def test_reasoning_content_field():
    events = collect(['data: {"choices":[{"delta":{"reasoning_content":"想"}}]}'])
    assert events == [("delta", {"content": "", "reasoning": "想"})]


def test_reasoning_field_fallback():
    # 没有 reasoning_content 时回退到 reasoning
    events = collect(['data: {"choices":[{"delta":{"reasoning":"think"}}]}'])
    assert events == [("delta", {"content": "", "reasoning": "think"})]


def test_done_marker():
    events = collect(['data: {"choices":[{"delta":{"content":"a"}}]}', "data: [DONE]"])
    assert events == [("delta", {"content": "a", "reasoning": ""}), ("done", {})]


def test_skip_blank_and_bad_lines():
    events = collect(["", "  ", ": keep-alive", "data: not-json", 'data: {"choices":[]}'])
    assert events == []


def test_empty_delta_skipped():
    events = collect(['data: {"choices":[{"delta":{}}]}'])
    assert events == []


def test_format_sse_shape():
    out = format_sse("delta", {"content": "中"})
    assert out == 'event: delta\ndata: {"content": "中"}\n\n'
