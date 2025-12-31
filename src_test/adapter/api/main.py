"""
COC 跑团游戏后端 API 主入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src_test.adapter.api.auth_router import router as auth_router
from src_test.adapter.api.chat_router import router as chat_router
from src_test.adapter.api.player_router import router as player_router

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


@app.get('/health')
def health_check():
    return {'status': 'ok', 'message': 'COC Backend API 服务运行中'}


if __name__ == '__main__':
    import uvicorn
    print("COC 跑团游戏后端服务")
    print("统一服务地址: http://localhost:5780")
    uvicorn.run(app, host='0.0.0.0', port=5780)
