from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("app")

async def global_exception_handler(request: Request, exc: Exception):
    """全局未捕获异常拦截器"""
    logger.error(f"全局拦截到未处理异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "code": 500,
            "message": "Internal Server Error",
            "detail": str(exc)
        }
    )