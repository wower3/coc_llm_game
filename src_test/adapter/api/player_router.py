"""
COC 玩家数据路由
提供角色信息、技能数据的查询接口
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["玩家数据"])


class SkillsRequest(BaseModel):
    """获取技能列表请求参数"""
    player_id: str
    min_value: int = 20


class SkillQueryRequest(BaseModel):
    """查询单个技能请求参数"""
    player_id: str
    query: str

# 延迟加载服务
_player_service = None


def get_service():
    """获取玩家服务实例"""
    global _player_service
    if _player_service is None:
        from src_test.service.player_service import get_player_service
        _player_service = get_player_service()
    return _player_service


@router.get('/player/{player_id}')
def get_player(player_id: str):
    """获取玩家基本信息"""
    try:
        service = get_service()
        player_info = service.get_player_info(player_id)

        if not player_info:
            raise HTTPException(status_code=404, detail='未找到该调查员')

        return {'success': True, 'data': player_info}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/skills')
def get_skills(request: SkillsRequest):
    """获取玩家技能信息（数值大于等于指定值的技能，默认20）"""
    try:
        service = get_service()
        filtered_skills = service.get_filtered_skills(request.player_id, min_value=request.min_value)
        return {'success': True, 'data': filtered_skills}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/chinese_name/{skill_id}')
def get_chinese_name(skill_id: str):
    """获取单个技能的中文名"""
    try:
        service = get_service()
        name = service.get_skill_chinese_name(skill_id)
        return {'success': True, 'data': {'id': skill_id, 'name': name}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/skill/query')
def query_skill_by_name_or_id(request: SkillQueryRequest):
    """通过技能中文名或ID查询玩家技能值"""
    try:
        service = get_service()
        skill_data = service.get_skill_value_by_name_or_id(request.player_id, request.query)
        if not skill_data:
            raise HTTPException(status_code=404, detail=f'未找到技能: {request.query}')
        return {'success': True, 'data': skill_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/equipments/{player_id}')
def get_equipments(player_id: str):
    """获取玩家装备列表"""
    try:
        service = get_service()
        equipments = service.get_player_equipments(player_id)
        return {'success': True, 'data': equipments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/health')
def health_check():
    """健康检查接口"""
    return {'status': 'ok', 'message': 'Player API 服务运行中'}
