import argparse
import uvicorn
from backend.app import create_app

app = create_app()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM 训练数据查看器")
    parser.add_argument("--port", type=int, default=8002, help="服务端口")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="监听地址")
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)
