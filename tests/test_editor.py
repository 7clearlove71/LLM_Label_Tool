import json
from backend.services.editor import update_row, delete_row, save_as

def test_update_row(sample_data_dir):
    path = str(sample_data_dir / "instruct.json")
    new_data = {"instruction": "新指令", "input": "新输入", "output": "新输出"}
    update_row(path, 0, new_data)
    with open(path, "r", encoding="utf-8") as f:
        first_line = f.readline().strip()
    assert json.loads(first_line) == new_data

def test_update_row_middle(sample_data_dir):
    path = str(sample_data_dir / "instruct.json")
    new_data = {"instruction": "中间修改", "input": "", "output": ""}
    update_row(path, 5, new_data)
    with open(path, "r", encoding="utf-8") as f:
        lines = [l for l in f if l.strip()]
    assert json.loads(lines[5].strip()) == new_data
    assert len(lines) == 10

def test_delete_row(sample_data_dir):
    path = str(sample_data_dir / "instruct.json")
    delete_row(path, 0)
    with open(path, "r", encoding="utf-8") as f:
        lines = [l for l in f if l.strip()]
    assert len(lines) == 9
    assert json.loads(lines[0].strip())["instruction"] == "指令1"

def test_save_as(sample_data_dir):
    source = str(sample_data_dir / "instruct.json")
    target = str(sample_data_dir / "instruct_copy.json")
    save_as(source, target)
    with open(target, "r", encoding="utf-8") as f:
        lines = [l for l in f if l.strip()]
    assert len(lines) == 10
