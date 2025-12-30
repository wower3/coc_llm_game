"""
COC 认证服务路由
提供JWT Token的生成和验证
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import jwt
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth", tags=["认证服务"])

# JWT配置
JWT_SECRET = "coc_game_secret_key_2024"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24


class LoginRequest(BaseModel):
    player_id: str


class TokenResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    player_id: Optional[str] = None
    message: Optional[str] = None


def create_token(player_id: str) -> str:
    """创建JWT Token"""
    payload = {
        "player_id": player_id,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[str]:
    """验证Token并返回player_id"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("player_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


@router.post('/login')
def login(data: LoginRequest):
    """登录并获取Token"""
    if not data.player_id or not data.player_id.strip():
        raise HTTPException(status_code=400, detail='玩家ID不能为空')

    token = create_token(data.player_id.strip())
    return TokenResponse(
        success=True,
        token=token,
        player_id=data.player_id.strip(),
        message='登录成功'
    )


@router.get('/verify')
def verify(authorization: Optional[str] = Header(None)):
    """从请求头验证Token并返回用户ID"""
    if not authorization:
        raise HTTPException(status_code=401, detail='未提供Token')

    # 支持 "Bearer xxx" 格式
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization

    player_id = verify_token(token)
    if not player_id:
        raise HTTPException(status_code=401, detail='Token无效或已过期')

    return TokenResponse(
        success=True,
        player_id=player_id,
        message='验证成功'
    )
