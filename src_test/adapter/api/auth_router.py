"""
COC 认证服务路由
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import jwt
from datetime import datetime, timedelta
from src_test.infrastructure.log import get_logger

logger = get_logger("API")

router = APIRouter(prefix="/auth", tags=["认证服务"])

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
    payload = {
        "player_id": player_id,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("player_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


@router.post('/login')
def login(data: LoginRequest):
    logger.info(f"[API] 用户登录请求: player_id={data.player_id}")
    try:
        if not data.player_id or not data.player_id.strip():
            logger.warning(f"[API] 登录失败: 玩家ID为空")
            raise HTTPException(status_code=400, detail='玩家ID不能为空')
        token = create_token(data.player_id.strip())
        logger.info(f"[API] 用户登录成功: player_id={data.player_id.strip()}")
        return TokenResponse(success=True, token=token, player_id=data.player_id.strip(), message='登录成功')
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] 登录异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail='登录失败')


@router.get('/verify')
def verify(authorization: Optional[str] = Header(None)):
    logger.debug("[API] Token验证请求")
    try:
        if not authorization:
            logger.warning("[API] Token验证失败: 未提供Token")
            raise HTTPException(status_code=401, detail='未提供Token')
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
        player_id = verify_token(token)
        if not player_id:
            logger.warning("[API] Token验证失败: Token无效或已过期")
            raise HTTPException(status_code=401, detail='Token无效或已过期')
        logger.info(f"[API] Token验证成功: player_id={player_id}")
        return TokenResponse(success=True, player_id=player_id, message='验证成功')
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Token验证异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail='验证失败')
