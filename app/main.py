from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
from datetime import datetime

from config.settings import settings
from app.routers import documents, health
from app.services.redis_client import vector_search
from app.models.schemas import ErrorResponse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于FastAPI和Redis的向量搜索API",
    debug=settings.debug
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc) if settings.debug else None,
            timestamp=datetime.now()
        ).model_dump()
    )


# 请求处理时间中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# 启动事件
async def startup_event():
    logger.info("Starting FastAPI application...")

    # 初始化Redis索引
    try:
        success = vector_search.create_index()
        if success:
            logger.info("Redis vector index initialized successfully")
        else:
            logger.error("Failed to initialize Redis vector index")
    except Exception as e:
        logger.error(f"Error initializing Redis: {e}")
        raise


# 关闭事件
async def shutdown_event():
    logger.info("Shutting down FastAPI application...")


# 注册事件处理器
app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)


# 根路径
@app.get("/")
async def root():
    return {
        "message": "FastAPI Redis Vector Search API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


# 包含路由
app.include_router(documents.router)
app.include_router(health.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )