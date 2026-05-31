from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.exceptions import global_exception_handler
from app.webhook import router as webhook_router  # 👈 导入 webhook 路由

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

    # 3. 【核心修复】在这里显式注册 Webhook 路由，确保它随 app 一起初始化
    app.include_router(webhook_router)

    # 4. 注册基础健康检查路由
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
    # 确保路径模块名称与运行方式匹配
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)