import shlex
from backend.models import RequestSpec, KeyValueItem

_DATA_FLAGS = ("-d", "--data", "--data-raw", "--data-binary", "--data-ascii")


def parse_curl(text: str) -> RequestSpec:
    # 去掉行末续行符
    text = text.replace("\\\r\n", " ").replace("\\\n", " ")
    tokens = shlex.split(text)
    if tokens and tokens[0] == "curl":
        tokens = tokens[1:]

    method = None
    url = None
    body = None
    headers: list[KeyValueItem] = []

    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in ("-X", "--request") and i + 1 < len(tokens):
            method = tokens[i + 1]
            i += 2
            continue
        if t in ("-H", "--header") and i + 1 < len(tokens):
            raw = tokens[i + 1]
            i += 2
            if ":" in raw:
                k, v = raw.split(":", 1)
                headers.append(KeyValueItem(key=k.strip(), value=v.strip()))
            continue
        if t in _DATA_FLAGS and i + 1 < len(tokens):
            body = tokens[i + 1]
            i += 2
            continue
        if t == "--url" and i + 1 < len(tokens):
            url = tokens[i + 1]
            i += 2
            continue
        if t.startswith("-"):
            # 未知 flag，跳过（MVP 不处理其携带的值）
            i += 1
            continue
        if url is None:
            url = t
        i += 1

    spec = RequestSpec(url=url or "", headers=headers)
    if method:
        spec.method = method.upper()
    elif body is not None:
        spec.method = "POST"

    if body is not None:
        spec.body = body
        content_type = next((h.value for h in headers if h.key.lower() == "content-type"), "")
        spec.body_type = "json" if "json" in content_type.lower() else "raw"

    return spec
