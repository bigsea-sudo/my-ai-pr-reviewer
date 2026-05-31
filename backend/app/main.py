from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.exceptions import global_exception_handler

def create_app() -> FastAPI:
    app = FastAPI(
        title="AI PR Reviewer API",
        description="基于大模型的自动代码评审系统后端服务",
        version="1.0.0"
    )

    # 1. 配置跨域中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. 注册全局异常处理器
    app.add_exception_handler(Exception, global_exception_handler)

    # 3. 注册基础健康检查路由
    @app.get("/health", tags=["Infrastructure"])
    async def health_check():
        return {
            "status": "healthy",
            "service": "my-ai-pr-reviewer-backend",
            "version": "1.0.0"
        }

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)