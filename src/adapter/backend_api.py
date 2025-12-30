"""
COC 跑团游戏后端 API 主入口
整合所有子路由，统一端口服务
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# 添加项目路径
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, src_dir)

# 导入子路由
from adapter.player_router import router as player_router
from adapter.chat_router import router as chat_router

app = FastAPI(
    title="COC Backend API",
    description="COC 跑团游戏后端统一 API 服务"
)

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册子路由
app.include_router(player_router)
app.include_router(chat_router)


@app.get('/health')
def health_check():
    """总健康检查接口"""
    return {
        'status': 'ok',
        'message': 'COC Backend API 服务运行中'
    }


if __name__ == '__main__':
    import uvicorn
    print("=" * 50)
    print("COC 跑团游戏后端服务")
    print("=" * 50)
    print("统一服务地址: http://localhost:5780")
    print("API文档: http://localhost:5780/docs")
    print("=" * 50)
    uvicorn.run(app, host='0.0.0.0', port=5780)
