import json
import os
import tempfile
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app import create_app

@pytest.fixture
def app():
    return create_app()

@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.fixture
def sample_data_dir(tmp_path):
    """创建包含示例训练数据的临时目录"""
    # SFT 对话数据
    sft_dir = tmp_path / "sft_data"
    sft_dir.mkdir()
    sft_file = sft_dir / "chat.jsonl"
    lines = [
        json.dumps({"id": i, "messages": [
            {"role": "system", "content": "你是一个有用的助手"},
            {"role": "user", "content": f"问题{i}"},
            {"role": "assistant", "content": f"回答{i}"}
        ]}, ensure_ascii=False)
        for i in range(25)
    ]
    sft_file.write_text("\n".join(lines) + "\n")

    # RL 偏好数据
    rl_dir = tmp_path / "rl_data"
    rl_dir.mkdir()
    rl_file = rl_dir / "preference.json"
    lines_rl = [
        json.dumps({"id": i, "prompt": f"提示{i}", "chosen": f"好回答{i}", "rejected": f"差回答{i}"}, ensure_ascii=False)
        for i in range(15)
    ]
    rl_file.write_text("\n".join(lines_rl) + "\n")

    # 指令数据
    instruct_file = tmp_path / "instruct.json"
    lines_inst = [
        json.dumps({"instruction": f"指令{i}", "input": f"输入{i}", "output": f"输出{i}"}, ensure_ascii=False)
        for i in range(10)
    ]
    instruct_file.write_text("\n".join(lines_inst) + "\n")

    return tmp_path
