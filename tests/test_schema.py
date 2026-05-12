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
    assert fields["messages"]["type"] == "array<object>"
    assert fields["messages"]["display"] == "detail"
    # 验证嵌套 children 递归检测
    children = {c["name"]: c for c in fields["messages"]["children"]}
    assert children["role"]["type"] == "string"
    assert children["content"]["type"] == "string"

def test_detect_preference_schema():
    rows = [
        {"id": 0, "prompt": "问题", "chosen": "好答案", "rejected": "差答案"},
    ]
    schema = detect_schema(rows)
    fields = {f["name"]: f for f in schema["fields"]}
    assert fields["chosen"]["type"] == "string"
    assert fields["rejected"]["type"] == "string"

def test_detect_instruction_schema():
    rows = [
        {"instruction": "翻译", "input": "hello", "output": "你好"},
    ]
    schema = detect_schema(rows)
    fields = {f["name"]: f for f in schema["fields"]}
    assert fields["instruction"]["type"] == "string"

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
    # 验证 object 的 children 递归检测
    children = {c["name"]: c for c in fields["meta"]["children"]}
    assert children["key1"]["type"] == "string"
    assert children["key2"]["type"] == "string"


def test_detect_deeply_nested():
    rows = [{"config": {"db": {"host": "localhost", "port": 5432}, "debug": True}}]
    schema = detect_schema(rows)
    fields = {f["name"]: f for f in schema["fields"]}
    config_children = {c["name"]: c for c in fields["config"]["children"]}
    assert config_children["debug"]["type"] == "boolean"
    assert config_children["db"]["type"] == "object"
    db_children = {c["name"]: c for c in config_children["db"]["children"]}
    assert db_children["host"]["type"] == "string"
    assert db_children["port"]["type"] == "number"

def test_detect_empty_rows():
    schema = detect_schema([])
    assert schema["fields"] == []
