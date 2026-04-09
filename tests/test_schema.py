from backend.services.schema import detect_schema

def test_detect_conversation_schema():
    rows = [
        {"id": 0, "messages": [{"role": "user", "content": "你好"}, {"role": "assistant", "content": "嗨"}]},
        {"id": 1, "messages": [{"role": "user", "content": "再见"}]},
    ]
    schema = detect_schema(rows)
    fields = {f["name"]: f for f in schema["fields"]}
    assert fields["id"]["type"] == "number"
    assert fields["id"]["display"] == "column"
    assert fields["messages"]["pattern"] == "conversation"
    assert fields["messages"]["display"] == "detail"

def test_detect_preference_schema():
    rows = [
        {"id": 0, "prompt": "问题", "chosen": "好答案", "rejected": "差答案"},
    ]
    schema = detect_schema(rows)
    fields = {f["name"]: f for f in schema["fields"]}
    assert fields["chosen"]["pattern"] == "preference"
    assert fields["rejected"]["pattern"] == "preference"

def test_detect_instruction_schema():
    rows = [
        {"instruction": "翻译", "input": "hello", "output": "你好"},
    ]
    schema = detect_schema(rows)
    fields = {f["name"]: f for f in schema["fields"]}
    assert fields["instruction"]["pattern"] == "instruction"

def test_detect_long_string():
    rows = [{"text": "a" * 200}]
    schema = detect_schema(rows)
    fields = {f["name"]: f for f in schema["fields"]}
    assert fields["text"]["display"] == "detail"

def test_detect_generic_object():
    rows = [{"meta": {"key1": "val1", "key2": "val2"}}]
    schema = detect_schema(rows)
    fields = {f["name"]: f for f in schema["fields"]}
    assert fields["meta"]["type"] == "object"
    assert fields["meta"]["display"] == "detail"

def test_detect_empty_rows():
    schema = detect_schema([])
    assert schema["fields"] == []
