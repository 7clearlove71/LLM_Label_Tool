import json
from backend.services.scanner import scan_directory

def test_scan_finds_json_files(sample_data_dir):
    tree = scan_directory(str(sample_data_dir))
    assert tree["type"] == "directory"
    names = {child["name"] for child in tree["children"]}
    assert "sft_data" in names
    assert "rl_data" in names
    assert "instruct.json" in names

def test_scan_nested_structure(sample_data_dir):
    tree = scan_directory(str(sample_data_dir))
    sft = next(c for c in tree["children"] if c["name"] == "sft_data")
    assert sft["type"] == "directory"
    chat = next(c for c in sft["children"] if c["name"] == "chat.jsonl")
    assert chat["type"] == "file"
    assert chat["path"].endswith("chat.jsonl")
    assert chat["size"] > 0

def test_scan_ignores_non_json(sample_data_dir):
    (sample_data_dir / "readme.txt").write_text("hello")
    tree = scan_directory(str(sample_data_dir))
    names = {child["name"] for child in tree["children"]}
    assert "readme.txt" not in names

def test_scan_nonexistent_dir():
    tree = scan_directory("/nonexistent/path/12345")
    assert tree is None
