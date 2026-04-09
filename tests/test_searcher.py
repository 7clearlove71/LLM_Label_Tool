import json
from backend.services.searcher import search_file

def test_search_keyword(sample_data_dir):
    path = str(sample_data_dir / "sft_data" / "chat.jsonl")
    results = search_file(path, keyword="问题3")
    assert len(results) == 1
    assert results[0]["row_index"] == 3

def test_search_keyword_multiple_matches(sample_data_dir):
    path = str(sample_data_dir / "sft_data" / "chat.jsonl")
    results = search_file(path, keyword="问题1")
    assert len(results) == 11

def test_search_with_field(sample_data_dir):
    path = str(sample_data_dir / "rl_data" / "preference.json")
    results = search_file(path, keyword="好回答5", field="chosen")
    assert len(results) == 1
    assert results[0]["data"]["chosen"] == "好回答5"

def test_search_no_match(sample_data_dir):
    path = str(sample_data_dir / "instruct.json")
    results = search_file(path, keyword="不存在的内容xyz")
    assert results == []
