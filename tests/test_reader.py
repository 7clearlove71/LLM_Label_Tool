import json
from backend.services.reader import read_file, read_file_all, get_line_count

def test_read_file_default_10(sample_data_dir):
    path = str(sample_data_dir / "sft_data" / "chat.jsonl")
    result = read_file(path, offset=0, limit=10)
    assert len(result["rows"]) == 10
    assert result["total"] == 25
    assert result["rows"][0]["id"] == 0

def test_read_file_offset(sample_data_dir):
    path = str(sample_data_dir / "sft_data" / "chat.jsonl")
    result = read_file(path, offset=20, limit=10)
    assert len(result["rows"]) == 5
    assert result["rows"][0]["id"] == 20

def test_read_file_all(sample_data_dir):
    path = str(sample_data_dir / "rl_data" / "preference.json")
    result = read_file_all(path)
    assert len(result["rows"]) == 15
    assert result["total"] == 15

def test_get_line_count(sample_data_dir):
    path = str(sample_data_dir / "sft_data" / "chat.jsonl")
    assert get_line_count(path) == 25

def test_read_empty_file(tmp_path):
    empty = tmp_path / "empty.json"
    empty.write_text("")
    result = read_file(str(empty), 0, 10)
    assert result["rows"] == []
    assert result["total"] == 0
