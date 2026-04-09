from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import scan

def create_app() -> FastAPI:
    app = FastAPI(title="LLM 训练数据查看器")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(scan.router)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app
