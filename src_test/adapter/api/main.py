"""
COC 跑团游戏后端 API 主入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src_test.infrastructure.log import get_logger

from src_test.adapter.api.auth_router import router as auth_router
from src_test.adapter.api.chat_router import router as chat_router
from src_test.adapter.api.player_router import router as player_router

logger = get_logger("API")

app = FastAPI(
    title="COC Backend API",
    description="COC 跑团游戏后端统一 API 服务"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(player_router)
app.include_router(chat_router)
app.include_router(auth_router)


@app.on_event("startup")
async def startup_event():
    """应用启动时预热数据库连接"""
    logger.info("[API] 应用启动，预热数据库连接...")
    try:
        from src_test.infrastructure.database import get_repository
        repo = get_repository()
        # 触发数据库连接初始化
        _ = repo.db
        logger.info("[API] 数据库连接预热完成")
    except Exception as e:
        logger.warning(f"[API] 数据库连接预热失败（将在首次请求时重试）: {e}")


@app.get('/health')
def health_check():
    logger.info("[API] 后端健康检查")
    return {'status': 'ok', 'message': 'COC Backend API 服务运行中'}


if __name__ == '__main__':
    import uvicorn
    logger.info("COC 跑团游戏后端服务启动")
    logger.info("统一服务地址: http://localhost:5780")
    uvicorn.run(app, host='0.0.0.0', port=5780)
